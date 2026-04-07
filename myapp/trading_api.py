"""
Trading Engine API Endpoints
Handles order placement, book tracking, and playback simulation logic.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET
from django.db.models import Sum, Q
from django.core.cache import cache
from django.db import transaction
from decimal import Decimal
import json

from myapp.models import Order, TradeExecution, Portfolio, CustomUser, NEPSEPrice
from myapp.services.matching_engine import MatchingEngine
from myapp.services.market_session import (
    is_market_open, get_market_status, get_nepal_time
)
from myapp.services.playback_engine import get_playback_state

@require_GET
def api_orderbook(request, symbol):
    """
    GET /api/orderbook/<symbol>/
    Returns aggregated Top 5 Bid and Top 5 Ask levels.
    """
    symbol = symbol.upper().strip()
    
    # Cache key (1 second TTL for real-time feel)
    cache_key = f'orderbook_{symbol}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    
    # Get open and partial orders for this symbol
    buy_orders = Order.objects.filter(
        symbol=symbol, side='BUY', status__in=['OPEN', 'PARTIAL']
    ).values('price').annotate(
        total_qty=Sum('qty') - Sum('filled_qty')
    ).order_by('-price')[:5]
    
    sell_orders = Order.objects.filter(
        symbol=symbol, side='SELL', status__in=['OPEN', 'PARTIAL']
    ).values('price').annotate(
        total_qty=Sum('qty') - Sum('filled_qty')
    ).order_by('price')[:5]
    
    response_data = {
        'success': True,
        'symbol': symbol,
        'bids': [{'price': float(o['price']), 'qty': int(o['total_qty'])} for o in buy_orders],
        'asks': [{'price': float(o['price']), 'qty': int(o['total_qty'])} for o in sell_orders],
        'last_updated': get_nepal_time().isoformat()
    }
    
    cache.set(cache_key, response_data, 1)
    return JsonResponse(response_data)


@require_GET
def api_market_session(request):
    """
    GET /api/market/session/
    Returns current market session status including playback mode flag.
    """
    status = get_market_status()
    state = get_playback_state()
    
    # Inject the playback flag so the frontend knows to show "Playback Mode"
    status['is_playback'] = state['is_playback']
    
    return JsonResponse({
        'success': True,
        'data': status
    })


from django.utils import timezone  # Ensure this is imported at the top

@require_GET
@login_required
def api_user_orders(request):
    """
    GET /api/trade/orders/
    Returns current user's open and partial orders.
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    qs = Order.objects.filter(user=request.user, status__in=['OPEN', 'PARTIAL'])
    
    if symbol:
        qs = qs.filter(symbol=symbol)
    
    data = [{
        'id': o.id,
        'symbol': o.symbol,
        'side': o.side,
        'qty': o.qty,
        'filled_qty': o.filled_qty,
        'remaining_qty': o.remaining_qty,
        'price': float(o.price),
        'status': o.status,
        # Updated to use local timezone based on settings.py (Asia/Kathmandu)
        'created_at': timezone.localtime(o.created_at).strftime('%Y-%m-%d %H:%M:%S'),
    } for o in qs.order_by('-created_at')[:100]]
    
    return JsonResponse({'success': True, 'data': data})

@require_http_methods(['POST'])
@login_required
def api_cancel_order(request, order_id):
    """
    POST /api/trade/cancel/<order_id>/
    Cancel an open order and refund Virtual Balance if it was a Buy order.
    """
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        if order.status not in ['OPEN', 'PARTIAL']:
            return JsonResponse({'success': False, 'message': 'Order already filled or cancelled.'})
        
        with transaction.atomic():
            if order.side == 'BUY':
                refund = Decimal(str(order.remaining_qty)) * order.price
                request.user.virtual_balance += refund
                request.user.save()
            
            order.status = 'CANCELLED'
            order.save()
        
        return JsonResponse({'success': True, 'message': 'Order successfully cancelled.'})
        
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found.'}, status=404)


@require_http_methods(['POST'])
@login_required
def api_place_order_new(request):
    """
    POST /api/trade/place-new/
    Main order matching logic. Notifies BOTH the Taker and the Maker(s) via email.
    """
    from .utils import send_trade_confirmation_email
    from myapp.models import CustomUser, Portfolio
    from django.db import transaction

    try:
        data = json.loads(request.body)
        symbol = (data.get('symbol') or '').strip().upper()
        side = (data.get('side') or '').strip().upper()
        order_type = (data.get('order_type') or 'LIMIT').strip().upper()
        
        try:
            qty = int(data.get('qty', 0))
            price = Decimal(str(data.get('price', 0)))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity or price format.'})
        
        # 1. Check Market / Playback Status
        state = get_playback_state()
        if not is_market_open() and not state['is_playback']:
            return JsonResponse({'success': False, 'message': 'Market is closed.'})
        
        # 2. Create and Validate Order
        order = Order(user=request.user, symbol=symbol, side=side, order_type=order_type, qty=qty, price=price, status='OPEN')
        is_valid, error_msg = MatchingEngine.validate_order(order)
        if not is_valid:
            return JsonResponse({'success': False, 'message': error_msg})
        
        # 3. Deduct Funds for BUY (locking capital)
        if side == 'BUY':
            total_cost = Decimal(str(qty)) * price
            request.user.virtual_balance -= total_cost
            request.user.save()
        
        order.save()
        
        # 4. Run Matching Engine
        executions = MatchingEngine.match_order(order)
        
        # 5. DEMO MAGIC: Playback Auto-Execution Bot
        if state['is_playback'] and not executions:
            pb_price_obj = NEPSEPrice.objects.filter(symbol=symbol, timestamp=state['timestamp']).first()
            if pb_price_obj and pb_price_obj.ltp:
                pb_ltp = float(pb_price_obj.ltp)
                if (side == 'BUY' and pb_ltp <= float(price)) or (side == 'SELL' and pb_ltp >= float(price)):
                    mm_user, _ = CustomUser.objects.get_or_create(
                        username='marketbot', 
                        email='bot@nepse.com', 
                        defaults={'virtual_balance': 999999999}
                    )
                    bot_side = 'SELL' if side == 'BUY' else 'BUY'
                    with transaction.atomic():
                        if bot_side == 'SELL':
                            Portfolio.objects.update_or_create(user=mm_user, symbol=symbol, defaults={'quantity': 999999, 'avg_price': 100})
                        bot_order = Order.objects.create(user=mm_user, symbol=symbol, side=bot_side, order_type='LIMIT', qty=order.remaining_qty, price=Decimal(str(pb_ltp)), status='OPEN')
                        execution = MatchingEngine.execute_trade(buy_order=order if side == 'BUY' else bot_order, sell_order=bot_order if side == 'BUY' else order, qty=order.remaining_qty, price=Decimal(str(pb_ltp)))
                        executions.append(execution)
        
        # 6. EMAIL NOTIFICATION LOGIC (The Fix)
        if executions:
            # --- A. Notify the person who just placed the order (The Taker) ---
            request.user.refresh_from_db()
            taker_qty = sum(e.executed_qty for e in executions)
            taker_avg_p = sum(e.executed_qty * float(e.executed_price) for e in executions) / taker_qty
            
            send_trade_confirmation_email(
                user=request.user, 
                symbol=symbol, 
                side=side, 
                qty=taker_qty, 
                price=taker_avg_p, 
                order_id=order.id, 
                order_type=order_type
            )

            # --- B. Notify the counter-parties (The Makers) ---
            for e in executions:
                # Determine who the counter-party is for this specific execution
                if side == 'BUY':
                    # Current user is Buyer, so counter-party is the Seller
                    maker_user = e.sell_order.user
                    maker_side = 'SELL'
                    maker_order_id = e.sell_order.id
                else:
                    # Current user is Seller, so counter-party is the Buyer
                    maker_user = e.buy_order.user
                    maker_side = 'BUY'
                    maker_order_id = e.buy_order.id

                # Don't send emails to the Market Bot
                if maker_user.username == 'marketbot':
                    continue

                # Refresh maker's data so the email shows updated balance/shares
                maker_user.refresh_from_db()

                send_trade_confirmation_email(
                    user=maker_user,
                    symbol=symbol,
                    side=maker_side,
                    qty=e.executed_qty,
                    price=float(e.executed_price),
                    order_id=maker_order_id,
                    order_type='LIMIT'
                )

            message = f'Trade success! {taker_qty} shares filled.'
        else:
            message = f'Order placed successfully! Waiting for match.'
            
        return JsonResponse({'success': True, 'message': message, 'executions': len(executions)})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f"Engine Error: {str(e)}"})

@require_GET
@login_required
def api_trade_executions(request):
    """
    GET /api/trade/executions/
    Returns history of filled trades for the current user.
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    
    qs = TradeExecution.objects.filter(
        Q(buy_order__user=request.user) | Q(sell_order__user=request.user)
    ).select_related('buy_order', 'sell_order')
    
    if symbol:
        qs = qs.filter(symbol=symbol)
    
    data = [{
        'executed_at': timezone.localtime(e.executed_at).strftime('%Y-%m-%d %H:%M:%S'),
        'symbol': e.symbol,
        'side': 'BUY' if e.buy_order.user == request.user else 'SELL',
        'qty': e.executed_qty,
        'price': float(e.executed_price),
        'status': 'FILLED'
    } for e in qs.order_by('-executed_at')[:200]]
    
    return JsonResponse({'success': True, 'data': data})
"""
New API endpoints for trading engine
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET
from django.db.models import Sum, Count
from django.core.cache import cache
from decimal import Decimal
import json

from myapp.models import Order, TradeExecution, Portfolio
from myapp.services.matching_engine import MatchingEngine
from myapp.services.market_session import (
    is_market_open, get_market_status, get_nepal_time
)


@require_GET
def api_orderbook(request, symbol):
    """
    GET /api/orderbook/<symbol>/
    Returns aggregated Top 5 Bid and Top 5 Ask levels
    """
    symbol = symbol.upper().strip()
    
    # Check cache first (1 second TTL)
    cache_key = f'orderbook_{symbol}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    
    # Get open and partial orders for this symbol
    buy_orders = Order.objects.filter(
        symbol=symbol,
        side='BUY',
        status__in=['OPEN', 'PARTIAL']
    ).values('price').annotate(
        total_qty=Sum('qty') - Sum('filled_qty')
    ).order_by('-price')[:5]  # Top 5 highest prices
    
    sell_orders = Order.objects.filter(
        symbol=symbol,
        side='SELL',
        status__in=['OPEN', 'PARTIAL']
    ).values('price').annotate(
        total_qty=Sum('qty') - Sum('filled_qty')
    ).order_by('price')[:5]  # Top 5 lowest prices
    
    # Format data
    bids = [{'price': float(o['price']), 'qty': int(o['total_qty'])} for o in buy_orders]
    asks = [{'price': float(o['price']), 'qty': int(o['total_qty'])} for o in sell_orders]
    
    response_data = {
        'success': True,
        'symbol': symbol,
        'bids': bids,  # Top 5 Buy orders
        'asks': asks,  # Top 5 Sell orders
        'last_updated': get_nepal_time().isoformat()
    }
    
    # Cache for 1 second
    cache.set(cache_key, response_data, 1)
    
    return JsonResponse(response_data)


@require_GET
def api_market_session(request):
    """
    GET /api/market/session/
    Returns current market session status
    """
    status = get_market_status()
    return JsonResponse({
        'success': True,
        'data': status
    })


@require_GET
@login_required
def api_user_orders(request):
    """
    GET /api/trade/orders/
    Returns user's open and partial orders
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    
    qs = Order.objects.filter(
        user=request.user,
        status__in=['OPEN', 'PARTIAL']
    )
    
    if symbol:
        qs = qs.filter(symbol=symbol)
    
    qs = qs.order_by('-created_at')[:100]
    
    data = [{
        'id': o.id,
        'symbol': o.symbol,
        'side': o.side,
        'qty': o.qty,
        'filled_qty': o.filled_qty,
        'remaining_qty': o.remaining_qty,
        'price': float(o.price),
        'status': o.status,
        'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    } for o in qs]
    
    return JsonResponse({'success': True, 'data': data})


@require_http_methods(['POST'])
@login_required
def api_cancel_order(request, order_id):
    """
    POST /api/trade/cancel/<order_id>/
    Cancel an open order
    """
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        if order.status not in ['OPEN', 'PARTIAL']:
            return JsonResponse({
                'success': False,
                'message': 'Order cannot be cancelled (already filled or cancelled)'
            })
        
        # Refund balance for BUY orders
        if order.side == 'BUY':
            remaining_cost = Decimal(str(order.remaining_qty)) * order.price
            order.user.virtual_balance += remaining_cost
            order.user.save()
        
        # Update order status
        order.status = 'CANCELLED'
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Order cancelled successfully. Refunded: Rs {remaining_cost:,.2f}' if order.side == 'BUY' else 'Order cancelled successfully.'
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)


@require_http_methods(['POST'])
@login_required
def api_place_order_new(request):
    """
    POST /api/trade/place/
    Place a new order with matching engine
    """
    try:
        data = json.loads(request.body)
        symbol = (data.get('symbol') or '').strip().upper()
        side = (data.get('side') or '').strip().upper()
        order_type = (data.get('order_type') or 'LIMIT').strip().upper()
        
        try:
            qty = int(data.get('qty', 0))
            # Price is optional for MARKET orders
            price_val = data.get('price')
            price = float(price_val) if price_val is not None else 0.0
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity or price.'})
        
        # Validate inputs
        if not symbol:
            return JsonResponse({'success': False, 'message': 'Symbol is required.'})
        
        if side not in ['BUY', 'SELL']:
            return JsonResponse({'success': False, 'message': 'Invalid side (BUY/SELL).'})
            
        if order_type not in ['LIMIT', 'MARKET', 'STOP_LOSS']:
            return JsonResponse({'success': False, 'message': 'Invalid order type.'})
        
        if qty <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be positive.'})
        
        if order_type == 'LIMIT' and price <= 0:
            return JsonResponse({'success': False, 'message': 'Price must be positive for limit orders.'})
        
        # Check market is open
        if not is_market_open():
            return JsonResponse({
                'success': False,
                'message': 'Market is closed. Trading hours: 11:00-15:00 Nepal Time'
            })
        
        # Create order object (not saved yet)
        order = Order(
            user=request.user,
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            price=Decimal(str(price)),
            status='OPEN'
        )
        
        # Validate order (this will set the price for MARKET orders based on LTP)
        is_valid, error_msg = MatchingEngine.validate_order(order)
        if not is_valid:
            return JsonResponse({'success': False, 'message': error_msg})
        
        # Deduct balance for BUY orders
        if side == 'BUY':
            total_cost = Decimal(str(qty)) * order.price
            order.user.virtual_balance -= total_cost
            order.user.save()
        
        # Save order
        order.save()
        
        # Try to match order
        executions = MatchingEngine.match_order(order)
        
        # Prepare response
        if executions:
            total_filled = sum(e.executed_qty for e in executions)
            avg_price = sum(e.executed_qty * float(e.executed_price) for e in executions) / total_filled if total_filled > 0 else 0
            
            message = f'Order placed! Filled {total_filled}/{qty} shares @ avg Rs {avg_price:.2f}'
        else:
            message = f'Order placed successfully! {side} {qty} {symbol} @ Rs {price:.2f} (waiting for match)'
        
        # Refresh order status
        order.refresh_from_db()
        
        # Add success message if notifications are enabled
        if request.user.buy_sell_notifications:
            from django.contrib import messages
            messages.success(request, f"✅ {side} order placed successfully for {symbol}")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'order': {
                'id': order.id,
                'status': order.status,
                'filled_qty': order.filled_qty,
                'remaining_qty': order.remaining_qty
            },
            'executions': len(executions)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
@login_required
def api_trade_executions(request):
    """
    GET /api/trade/executions/
    Returns user's trade executions (completed trades)
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    
    # Get executions where user was buyer or seller
    from django.db.models import Q
    
    qs = TradeExecution.objects.filter(
        Q(buy_order__user=request.user) | Q(sell_order__user=request.user)
    ).select_related('buy_order', 'sell_order')
    
    if symbol:
        qs = qs.filter(symbol=symbol)
    
    qs = qs.order_by('-executed_at')[:200]
    
    data = []
    for e in qs:
        # Determine if user was buyer or seller
        if e.buy_order.user == request.user:
            side = 'BUY'
        else:
            side = 'SELL'
        
        data.append({
            'executed_at': e.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': e.symbol,
            'side': side,
            'qty': e.executed_qty,
            'price': float(e.executed_price),
            'status': 'FILLED'
        })
    
    return JsonResponse({'success': True, 'data': data})

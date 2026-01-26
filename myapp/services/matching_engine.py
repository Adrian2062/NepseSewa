"""
Matching Engine Service
Implements price-time priority order matching algorithm
"""
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from myapp.models import Order, Portfolio, TradeExecution, CustomUser


class MatchingEngine:
    """
    Core matching engine with price-time priority.
    Best bid (highest) matches best ask (lowest).
    Supports partial fills.
    """
    
    @staticmethod
    @transaction.atomic
    def match_order(order):
        """
        Main entry point for matching a new order.
        Returns list of trade executions created.
        """
        executions = []
        
        # Find matching orders
        matching_orders = MatchingEngine.find_matching_orders(order)
        
        for match_order in matching_orders:
            if order.remaining_qty <= 0:
                break
            
            # Calculate execution quantity
            exec_qty = min(order.remaining_qty, match_order.remaining_qty)
            
            # Determine execution price (use the resting order's price)
            exec_price = match_order.price
            
            # Execute the trade
            execution = MatchingEngine.execute_trade(
                buy_order=order if order.side == 'BUY' else match_order,
                sell_order=match_order if order.side == 'BUY' else order,
                qty=exec_qty,
                price=exec_price
            )
            
            executions.append(execution)
        
        return executions
    
    @staticmethod
    def find_matching_orders(order):
        """
        Find counter-party orders that can match.
        Returns orders sorted by price-time priority.
        """
        # Find opposite side orders for same symbol
        counter_side = 'SELL' if order.side == 'BUY' else 'BUY'
        
        # Get open or partial orders
        candidates = Order.objects.filter(
            symbol=order.symbol,
            side=counter_side,
            status__in=['OPEN', 'PARTIAL']
        ).select_for_update()
        
        # Apply price filter
        if order.side == 'BUY':
            # Buy order matches sell orders at or below buy price
            candidates = candidates.filter(price__lte=order.price)
            # Sort: lowest price first (best for buyer), then oldest first
            candidates = candidates.order_by('price', 'created_at')
        else:
            # Sell order matches buy orders at or above sell price
            candidates = candidates.filter(price__gte=order.price)
            # Sort: highest price first (best for seller), then oldest first
            candidates = candidates.order_by('-price', 'created_at')
        
        return list(candidates)
    
    @staticmethod
    @transaction.atomic
    def execute_trade(buy_order, sell_order, qty, price):
        """
        Execute a trade between buy and sell orders.
        Updates orders, wallets, portfolios, and creates execution record.
        """
        # Lock users for update to prevent race conditions
        buyer = CustomUser.objects.select_for_update().get(id=buy_order.user_id)
        seller = CustomUser.objects.select_for_update().get(id=sell_order.user_id)
        
        # Update order filled quantities
        buy_order.filled_qty = F('filled_qty') + qty
        buy_order.save()
        buy_order.refresh_from_db()
        
        sell_order.filled_qty = F('filled_qty') + qty
        sell_order.save()
        sell_order.refresh_from_db()
        
        # Update order statuses
        if buy_order.is_fully_filled:
            buy_order.status = 'FILLED'
            buy_order.save()
        elif buy_order.filled_qty > 0:
            buy_order.status = 'PARTIAL'
            buy_order.save()
        
        if sell_order.is_fully_filled:
            sell_order.status = 'FILLED'
            sell_order.save()
        elif sell_order.filled_qty > 0:
            sell_order.status = 'PARTIAL'
            sell_order.save()
        
        # Update wallets
        MatchingEngine.update_wallets(buyer, seller, qty, price, buy_order.price)
        
        # Update portfolios
        MatchingEngine.update_portfolios(buyer, seller, buy_order.symbol, qty, price)
        
        # Create trade execution record
        execution = TradeExecution.objects.create(
            buy_order=buy_order,
            sell_order=sell_order,
            symbol=buy_order.symbol,
            executed_qty=qty,
            executed_price=price
        )
        
        return execution
    
    @staticmethod
    def update_wallets(buyer, seller, qty, price, buyer_limit_price=None):
        """
        Update user wallets after trade execution.
        Buyer already paid matched cost (at limit price) when placing order.
        If executed price < limit price, refund the difference.
        Seller receives executed_price * qty.
        """
        total_executed_value = Decimal(str(qty)) * Decimal(str(price))
        
        # Seller receives payment
        seller.virtual_balance = F('virtual_balance') + total_executed_value
        seller.save()
        seller.refresh_from_db()
        
        # Buyer Refund Logic
        if buyer_limit_price and buyer_limit_price > price:
            refund_per_share = Decimal(str(buyer_limit_price)) - Decimal(str(price))
            total_refund = refund_per_share * Decimal(str(qty))
            
            if total_refund > 0:
                buyer.virtual_balance = F('virtual_balance') + total_refund
                buyer.save()
                buyer.refresh_from_db()
    
    @staticmethod
    def update_portfolios(buyer, seller, symbol, qty, price):
        """
        Update user portfolios after trade execution.
        Buyer gains shares, seller loses shares.
        """
        price_decimal = Decimal(str(price))
        qty_decimal = Decimal(str(qty))
        
        # Update buyer's portfolio (add shares)
        buyer_portfolio, created = Portfolio.objects.select_for_update().get_or_create(
            user=buyer,
            symbol=symbol,
            defaults={'quantity': qty, 'avg_price': price_decimal}
        )
        
        if not created:
            # Calculate new average price (Weighted Average)
            old_qty = Decimal(str(buyer_portfolio.quantity))
            old_avg = buyer_portfolio.avg_price
            total_qty = old_qty + qty_decimal
            
            new_avg_price = ((old_qty * old_avg) + (qty_decimal * price_decimal)) / total_qty
            
            buyer_portfolio.quantity = int(total_qty)
            buyer_portfolio.avg_price = new_avg_price.quantize(Decimal('0.01'))
            buyer_portfolio.save(update_fields=['quantity', 'avg_price', 'updated_at'])
        
        # Update seller's portfolio (remove shares)
        try:
            seller_portfolio = Portfolio.objects.select_for_update().get(user=seller, symbol=symbol)
            new_qty = seller_portfolio.quantity - qty
            
            if new_qty <= 0:
                seller_portfolio.delete()
            else:
                seller_portfolio.quantity = new_qty
                seller_portfolio.save(update_fields=['quantity', 'updated_at'])
        except Portfolio.DoesNotExist:
            # Should not happen with validation, but we'll log it or ignore
            pass
    
    @staticmethod
    def validate_order(order):
        """
        Validate order before placing.
        Returns (is_valid, error_message)
        """
        # Check user balance for BUY orders
        if order.side == 'BUY':
            total_cost = Decimal(str(order.qty)) * Decimal(str(order.price))
            if order.user.virtual_balance < total_cost:
                return False, f"Insufficient balance. Required: Rs {total_cost:,.2f}, Available: Rs {order.user.virtual_balance:,.2f}"
        
        # Check user holdings for SELL orders
        elif order.side == 'SELL':
            try:
                portfolio = Portfolio.objects.get(user=order.user, symbol=order.symbol)
                if portfolio.quantity < order.qty:
                    return False, f"Insufficient holdings. Required: {order.qty}, Available: {portfolio.quantity}"
            except Portfolio.DoesNotExist:
                return False, f"You don't own any {order.symbol} shares"
        
        return True, None

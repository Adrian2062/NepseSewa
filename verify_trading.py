import os
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Order, NEPSEPrice, CustomUser, Portfolio, TradeExecution
from myapp.services.matching_engine import MatchingEngine

def test_trading_logic():
    print("--- Starting Trading Logic Verification ---")
    
    # Setup test data
    symbol = 'TEST_TICKER'
    user1, _ = CustomUser.objects.get_or_create(email='user1@example.com', defaults={'username': 'user1', 'virtual_balance': 100000})
    user2, _ = CustomUser.objects.get_or_create(email='user2@example.com', defaults={'username': 'user2', 'virtual_balance': 100000})
    
    # Ensure balance for testing
    user1.virtual_balance = 100000
    user1.save()
    user2.virtual_balance = 100000
    user2.save()
    
    # 1. Create LTP for symbol
    ltp = 100.0
    NEPSEPrice.objects.update_or_create(
        symbol=symbol,
        defaults={'ltp': ltp, 'timestamp': timezone.now()}
    )
    print(f"Set LTP for {symbol} to Rs {ltp}")

    # 2. Test Limit Order Price Enforcement (BUY too high)
    bad_buy_price = 110.0 # > 105.0
    order_buy_bad = Order(user=user1, symbol=symbol, side='BUY', order_type='LIMIT', qty=10, price=Decimal(str(bad_buy_price)))
    is_valid, msg = MatchingEngine.validate_order(order_buy_bad)
    print(f"Validating BUY LIMIT at {bad_buy_price}: {'PASS' if is_valid else 'FAIL'} - {msg}")

    # 3. Test Limit Order Price Enforcement (SELL too low)
    # Add holdings first
    Portfolio.objects.update_or_create(user=user2, symbol=symbol, defaults={'quantity': 100, 'avg_price': 100.0})
    bad_sell_price = 90.0 # < 95.0
    order_sell_bad = Order(user=user2, symbol=symbol, side='SELL', order_type='LIMIT', qty=10, price=Decimal(str(bad_sell_price)))
    is_valid, msg = MatchingEngine.validate_order(order_sell_bad)
    print(f"Validating SELL LIMIT at {bad_sell_price}: {'PASS' if is_valid else 'FAIL'} - {msg}")

    # 4. Test Market Order Buy
    order_market_buy = Order(user=user1, symbol=symbol, side='BUY', order_type='MARKET', qty=10, price=Decimal('0'))
    is_valid, msg = MatchingEngine.validate_order(order_market_buy)
    print(f"Validating BUY MARKET: {'PASS' if is_valid else 'FAIL'} - Price set to: {order_market_buy.price}")

    # 5. Test Market Order matching against existing Limit Order
    # Create a sell limit order at Rs 102 (within range)
    sell_order = Order.objects.create(user=user2, symbol=symbol, side='SELL', order_type='LIMIT', qty=5, price=Decimal('102.0'), status='OPEN')
    print(f"Placed SELL LIMIT for 5 shares at Rs 102.0")
    
    # Place a market buy for 5 shares
    market_buy = Order(user=user1, symbol=symbol, side='BUY', order_type='MARKET', qty=5, price=Decimal('0'))
    is_valid, _ = MatchingEngine.validate_order(market_buy)
    market_buy.save()
    
    executions = MatchingEngine.match_order(market_buy)
    print(f"Matched MARKET BUY: Executed {len(executions)} trades")
    for e in executions:
        print(f"  Trade: {e.executed_qty} shares @ Rs {e.executed_price}")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    test_trading_logic()

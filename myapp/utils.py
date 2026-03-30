from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import pytz

def send_trade_confirmation_email(user, symbol, side, qty, price, order_id, order_type):
    from .models import Portfolio
    
    # 1. Nepali Time Setup
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    nepal_time = timezone.now().astimezone(nepal_tz).strftime('%b %d, %Y | %I:%M %p')

    # 2. Calculations
    total_amount = float(qty) * float(price)
    portfolio_item = Portfolio.objects.filter(user=user, symbol=symbol).first()
    new_total_shares = portfolio_item.quantity if portfolio_item else 0
    total_wealth = float(user.virtual_balance) + float(user.portfolio_value)
    weight = ( (new_total_shares * float(price)) / total_wealth * 100 ) if total_wealth > 0 else 0

    # 3. Create Context for Template
    # Inside your utils.py confirmation function
    context = {
        'user_name': user.first_name.upper() or user.username.upper(),
        'symbol': symbol,
        'side': side.upper(),
        'qty': qty,
        'price': f"{float(price):,.2f}",
        'total_amount': f"{float(total_amount):,.2f}",
        'order_id': order_id,
        'nepal_time': nepal_time,
        'new_total_shares': new_total_shares,
        'remaining_cash': f"{float(user.virtual_balance):,.2f}",
        'weight': f"{weight:.2f}",
        'base_url': settings.BASE_URL
    }

    # 4. Render HTML
    html_content = render_to_string('emails/trade_confirmation.html', context)

    # 5. Send Email
    subject = f"Trade Confirmed: {side.upper()} {qty} {symbol}"
    email = EmailMessage(
        subject,
        "", # Plain text body
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.content_subtype = "html" # Tell Django this is HTML
    email.body = html_content
    
    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Email Error: {e}")
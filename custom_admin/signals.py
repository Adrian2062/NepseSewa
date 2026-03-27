from django.db.models.signals import post_save
from django.dispatch import receiver
from myapp.models import TradeExecution, UserSubscription, PaymentTransaction
from .models import Notification

# 1. THE MATCHING ENGINE SIGNAL
@receiver(post_save, sender=TradeExecution)
def notify_matching_engine_execution(sender, instance, created, **kwargs):
    if created:
        buyer_email = instance.buy_order.user.email
        seller_email = instance.sell_order.user.email
        
        # Changed 'category' to 'type'
        Notification.objects.create(
            user=None, # Global notification
            type='system', 
            title=f"Match Found: {instance.symbol}",
            message=(
                f"Matching Engine Success! {instance.executed_qty} units of {instance.symbol} "
                f"traded at Rs.{instance.executed_price}. "
                f"Buyer: {buyer_email} | Seller: {seller_email}"
            )
        )

# 2. MEMBERSHIP ACTIVATION SIGNAL
@receiver(post_save, sender=PaymentTransaction)
def notify_payment_success(sender, instance, created, **kwargs):
    if instance.status == 'COMPLETED':
        Notification.objects.create(
            user=instance.user, # Notify the specific user
            type='membership',  # Changed 'category' to 'type'
            title="Membership Activated 👑",
            message=f"Success! You have paid Rs.{instance.amount} for the {instance.plan.name} plan."
        )

# 3. MEMBERSHIP EXPIRY SIGNAL
@receiver(post_save, sender=UserSubscription)
def notify_subscription_status(sender, instance, created, **kwargs):
    if not created and (not instance.is_active or instance.is_expired):
        Notification.objects.create(
            user=instance.user, # Notify the specific user
            type='membership',
            title="Membership Expired ⚠️",
            message="Access Alert: Your subscription has expired. Please renew."
        )
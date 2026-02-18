import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

def test_email_sending():
    print("--- Django Email Debugger ---")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    subject = 'NepseSewa SMTP Test'
    message = 'If you are reading this, your Django SMTP configuration is working correctly!'
    recipient_list = [settings.EMAIL_HOST_USER]  # Send to yourself
    
    try:
        print("\nAttempting to send test email...")
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        if result:
            print("SUCCESS: Email sent successfully!")
        else:
            print("FAILURE: send_mail returned 0 (no email sent).")
            
    except Exception as e:
        print(f"\nERROR: Email sending failed!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        if "SMTPAuthenticationError" in str(e):
            print("\nSUGGESTION: This is likely an authentication issue.")
            print("1. Check if 'App Passwords' are enabled for your Gmail.")
            print("2. Ensure the 16-character App Password is correct.")
            print("3. Verify that 2-Step Verification is enabled on your Google account.")
        elif "TimeoutError" in str(e) or "ConnectionRefusedError" in str(e):
            print("\nSUGGESTION: Connection timed out.")
            print("1. Check your internet connection.")
            print("2. Verify if your network/ISP blocks port 465 or 587.")
            print("3. Ensure EMAIL_PORT and EMAIL_USE_TLS/SSL match (465/SSL or 587/TLS).")

if __name__ == "__main__":
    test_email_sending()

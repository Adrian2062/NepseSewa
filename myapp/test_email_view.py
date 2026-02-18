from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
import smtplib

def test_email_view(request):
    User = get_user_model()
    users = list(User.objects.values_list('email', flat=True))
    
    debug_info = [
        "<h1>Email Diagnostic</h1>",
        f"<strong>Registered Emails in DB:</strong> {', '.join(users) if users else 'No users found'}<br><br>"
    ]
    
    try:
        send_mail(
            'Test Email from NepseSewa',
            'If you receive this, SMTP is working.',
            'adrianpoudyal@gmail.com',
            ['adrianpoudyal@gmail.com'],
            fail_silently=False,
        )
        debug_info.append("<h2 style='color:green'>✅ Test Email Sent Successfully!</h2>")
        debug_info.append("Check your inbox (adrianpoudyal@gmail.com) for a test message.")
    except Exception as e:
        debug_info.append(f"<h2 style='color:red'>❌ Email Failed</h2>")
        debug_info.append(f"<strong>Error:</strong> {str(e)}")
        
    return HttpResponse("".join(debug_info))

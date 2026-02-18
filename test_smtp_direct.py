import smtplib
from email.mime.text import MIMEText

def test_smtp():
    host = 'smtp.gmail.com'
    port = 465
    user = 'adrianpoudyal@gmail.com'
    password = 'pzcnkgpfmbfhqseb'
    
    print(f"Connecting to {host}:{port}...")
    try:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
        print("Connected!")
        
        print(f"Logging in as {user}...")
        server.login(user, password)
        print("Logged in successfully!")
        
        msg = MIMEText("SMTP test successful.")
        msg['Subject'] = 'SMTP Test'
        msg['From'] = user
        msg['To'] = user
        
        print("Sending test email...")
        server.sendmail(user, [user], msg.as_string())
        print("Email sent!")
        
        server.quit()
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_smtp()

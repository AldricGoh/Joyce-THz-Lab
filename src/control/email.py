# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage

def send_notification(email_address,
                      subject=f'THz scan job finished ✅',
                      message="Your program has completed successfully."):
    msg = EmailMessage()
    msg.set_content(message)

    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_address

    # Send the message via UIS SMTP server.
    s = smtplib.SMTP('smtp.cam.ac.uk', 25)
    s.send_message(msg)
    s.quit()
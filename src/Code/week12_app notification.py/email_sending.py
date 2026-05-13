import smtplib
import email.mime.multipart
from email.mime.text import MIMEText

user_name = "Thanawat Lhuangwirot"
user_email = 'thanawatlhuangwirot@gmail.com'
gmail_password = 'pjaw cufa bgax xfqj'
target_name = "Thanawat Lhuangwirot"
target_email = "thanawat.lue@gpo.or.th"
message = "This is the body of the Email Test message."

def send_email(user_name, user_email, gmail_password, target_name, target_email, message):
  
    try:
        msg = email.mime.multipart.MIMEMultipart()
        msg['to'] = f'{target_name}<{target_email}>' 
        msg['from'] = f'{user_name}<{user_email}>' 
        msg['subject'] = 'Email Test'
        msg.add_header('reply-to', user_email) 
        msg.attach(MIMEText(message, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(user_email, gmail_password)
        message = msg.as_string() 
        session.sendmail(user_email, target_email, message)
        session.quit()
        print('Email sent.')
    except Exception as e:
        print('Email failed to send.')
        print(e)

# send_email(user_name, user_email, gmail_password, target_name, target_email, message)
import smtplib
import email.mime.multipart
from email.mime.text import MIMEText

def send_email(message):
    gmail_user = 'pramote.kuacharoen@gmail.com'
    gmail_password = 'cjaryjgzkzjbatvp'
    
    try:
        msg = email.mime.multipart.MIMEMultipart()
        msg['to'] = 'Pramote Kuacharoen<pramote@as.nida.ac.th>' 
        msg['from'] = 'Pramote Kuacharoen<pramote.kuacharoen@gmail.com>' 
        msg['subject'] = 'Email Test'
        msg.add_header('reply-to', 'pramote.kuacharoen@gmail.com') 
        msg.attach(MIMEText(message, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(gmail_user, gmail_password)
        message = msg.as_string() 
        session.sendmail('pramote.kuacharoen@gmail.com', 'pramote@as.nida.ac.th', message)
        session.quit()
        print('Email sent.')
    except Exception as e:
        print('Email failed to send.')
        print(e)

send_email('This is the body of the Email Test message.')
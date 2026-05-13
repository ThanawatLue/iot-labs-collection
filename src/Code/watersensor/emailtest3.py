import smtplib
import ssl
from email.message import EmailMessage
import datetime

email_sender = 'pramote.kuacharoen@gmail.com'
email_password = 'cjaryjgzkzjbatvp'
email_receiver = 'pramote@as.nida.ac.th'

subject = 'Water Sensor Alert'
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
body = f'{current_datetime} : Water Detected '

em = EmailMessage()
em['From'] = email_sender
em['To'] = email_receiver
em['Subject'] = subject
em.set_content(body)



context = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(email_sender, email_password)
    smtp.sendmail(email_sender, email_receiver, em.as_string())

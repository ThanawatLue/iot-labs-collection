
from gpiozero import InputDevice
import time
import smtplib
import ssl
from email.message import EmailMessage
import datetime


pin = InputDevice(17, pull_up=True)  

alert_trigger = False

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


while True:
    if pin.is_active:
        print("Water detected")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
    else:
        print("No water detected")
        
    time.sleep(1)

from gpiozero import Servo, MCP3008, Button, LED, Buzzer
from time import sleep
import signal
from email_sending import send_email

user_name = "Thanawat Lhuangwirot"
user_email = 'thanawatlhuangwirot@gmail.com'
gmail_password = 'pjaw cufa bgax xfqj'
target_name = "Thanawat Lhuangwirot"
target_email = "thanawat.lue@gpo.or.th"

print("Vitral Sign Alert System is running...")

led_HeartRate = LED(17)    
led_BloodSugar = LED(27)    
led_BloodPressure = LED(22)
HeartRate_sensor = MCP3008(channel = 0)
BloodSugar_sensor = MCP3008(channel = 1)  
BloodPressure_sensor = MCP3008(channel = 2)

hr_alert_sent = False
bs_alert_sent = False
bp_alert_sent = False

email_cooldown = 120 # ส่งทุกๆ 1 นาที 120 * 0.5

hr_cooldown = 0
bs_cooldown = 0
bp_cooldown = 0

def main():
    global hr_alert_sent, bs_alert_sent, bp_alert_sent
    global hr_cooldown, bs_cooldown, bp_cooldown
    
    print("System active. Press Ctrl+C to exit.")

    while True:
        # อัพเดตตัวนับ cooldown
        if hr_cooldown > 0:
            hr_cooldown -= 1
        if bs_cooldown > 0:
            bs_cooldown -= 1
        if bp_cooldown > 0:
            bp_cooldown -= 1
            
        # HeartRate_sensor (if more than 120 bpm, send email notify user, max 300 bpm)
        HR = HeartRate_sensor.value
        print(f"Heart Rate: {HR:.2f} ({int(HR * 300)} BPM)")  
    
        if HR >= 0.4:  
            led_HeartRate.on()
            if not hr_alert_sent and hr_cooldown == 0:
                HR_message = f"ALERT: High Heart Rate detected! Current value: {int(HR * 300)} BPM ({HR:.2f})"
                send_email(user_name, user_email, gmail_password, target_name, target_email, HR_message)
                hr_alert_sent = True
                hr_cooldown = email_cooldown
                print("Heart Rate alert ")
        else:
            led_HeartRate.off()
            if hr_alert_sent and hr_cooldown == 0:
                # HR_normal_message = f"NORMAL: Heart Rate returned to normal: {int(HR * 300)} BPM ({HR:.2f})"
                # send_email(user_name, user_email, gmail_password, target_name, target_email, HR_normal_message)
                hr_alert_sent = False
                hr_cooldown = email_cooldown
                # print("Heart Rate normal email sent!")

        # BloodSugar_sensor (if more than 200 mg/dl, send email notify user, max 400 mg/dl)
        BS = BloodSugar_sensor.value
        print(f"Blood Sugar: {BS:.2f} ({int(BS * 400)} mg/dl)")  
        
        if BS >= 0.5:  
            led_BloodSugar.on()
            if not bs_alert_sent and bs_cooldown == 0:
                BS_message = f"ALERT: High Blood Sugar detected! Current value: {int(BS * 400)} mg/dl ({BS:.2f})"
                send_email(user_name, user_email, gmail_password, target_name, target_email, BS_message)
                bs_alert_sent = True
                bs_cooldown = email_cooldown
                print("Blood Sugar alert email sent!")
        else:
            led_BloodSugar.off()
            if bs_alert_sent and bs_cooldown == 0:
                # BS_normal_message = f"NORMAL: Blood Sugar returned to normal: {int(BS * 400)} mg/dl ({BS:.2f})"
                # send_email(user_name, user_email, gmail_password, target_name, target_email, BS_normal_message)
                bs_alert_sent = False
                bs_cooldown = email_cooldown
                # print("Blood Sugar normal email sent!")

        # BloodPressure_sensor (if more than 140 mmHg, send email notify user, for max 300 mmHg)
        BP = BloodPressure_sensor.value
        print(f"Blood Pressure: {BP:.2f} ({int(BP * 300)} mmHg)")  
        
        if BP >= 0.47: 
            led_BloodPressure.on()
            if not bp_alert_sent and bp_cooldown == 0:
                BP_message = f"ALERT: High Blood Pressure detected! Current value: {int(BP * 300)} mmHg ({BP:.2f})"
                send_email(user_name, user_email, gmail_password, target_name, target_email, BP_message)
                bp_alert_sent = True
                bp_cooldown = email_cooldown
                print("Blood Pressure alert email sent!")
        else:
            led_BloodPressure.off()
            if bp_alert_sent and bp_cooldown == 0:
                # BP_normal_message = f"NORMAL: Blood Pressure returned to normal: {int(BP * 300)} mmHg ({BP:.2f})"
                # send_email(user_name, user_email, gmail_password, target_name, target_email, BP_normal_message)
                bp_alert_sent = False
                bp_cooldown = email_cooldown
                # print("Blood Pressure normal email sent!")
        
        sleep(0.5)

if __name__ == "__main__":
    main()
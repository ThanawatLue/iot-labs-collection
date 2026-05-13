from gpiozero import PWMLED, Motor, Servo, MCP3008, Button
from time import sleep

print("Analog Control is running...")

led = PWMLED(21)
motor = Motor(22, 23)
servo = Servo(24)
potentiometer1 = MCP3008(0)  
potentiometer2 = MCP3008(2)  
potentiometer3 = MCP3008(6) 
switch = Button(15)        


while True:
    led.value = potentiometer1.value
  
    if switch.is_pressed:
        motor.forward(potentiometer2.value) 
    else:
        motor.backward(potentiometer2.value) 
    
    servo.value = 1 - 2 * potentiometer3.value
    
    sleep(0.05)
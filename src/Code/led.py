from gpiozero import LED, Button
from time import sleep

led1 = LED(21)
led1.blink()

led2 = LED(22)


def button_pressed():
    print('Button Pressed!')
    led2.toggle()


button = Button(11)
button.when_pressed = button_pressed

while True:
    sleep(0.1)

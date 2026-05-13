from gpiozero import MotionSensor, LED
from signal import pause

pir = MotionSensor(4)
led = LED(16)

pir.when_activated = led.on
pir.when_deactivated = led.off

# pir2 = MotionSensor(5)
# led2 = LED(17)

# pir2.when_activated = led2.on
# pir2.when_deactivated = led2.off


pause()

# controller.py

import pyfirmata
import time

board = pyfirmata.Arduino('COM5')
led = board.get_pin('d:13:o')
time.sleep(2)  # Wait for the Arduino to initialize

def blink_led(val):
    # Blink the LED once
    led.write(1)
    time.sleep(val)
    led.write(0)

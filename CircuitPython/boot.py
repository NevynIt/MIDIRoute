import storage
import board
import digitalio
import time

# Set up the button
button = digitalio.DigitalInOut(board.BUTTON)  # Use a GPIO pin for the button
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

time.sleep(0.1)

print("Button is pressed:", not button.value)

# Check if the button is pressed
if button.value:  # Button is pressed
    storage.disable_usb_drive()  # Disable USB drive
    storage.remount("/", readonly=False)  # Remount the filesystem as writable
import board
import busio
import time
import json
import supervisor
import usb_midi
import digitalio
import storage
import microcontroller

# Set up the button
button = digitalio.DigitalInOut(board.BUTTON)  # Use a GPIO pin for the button
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# Set up the LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

if storage.getmount("/").readonly:
    led.value = True

CONFIG_FILE = "/config.json"

# Default configuration values
default_config = {
    "uart_baud": 1500000,  # baud rate for UART
    "uart_tx": "GP0",     # TX pin name (as defined in board)
    "uart_rx": "GP1"      # RX pin name (as defined in board)
}

def save_config():
    """Save the current configuration to the CONFIG_FILE."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print("Configuration saved:", config)
    except Exception as e:
        print("Error saving configuration:", e)

# Global configuration dictionary
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    print("Loaded configuration:", config)
except Exception as e:
    print("Config load error or file missing, using defaults:", e)
    config = default_config.copy()
    save_config()

# Global UART object. It will be initialized using init_uart().
uart = None
verbose = False

def init_uart():
    """Initialize (or reinitialize) the UART using the current configuration."""
    global uart
    # If uart already exists, deinitialize it (if supported)
    try:
        if uart is not None:
            uart.deinit()
    except Exception:
        pass
    # Get pin objects using board.<pinname>
    try:
        tx_pin = getattr(board, config["uart_tx"])
        rx_pin = getattr(board, config["uart_rx"])
    except AttributeError as e:
        print("Error: Invalid pin name in configuration:", e)
        return
    baud = config["uart_baud"]
    uart = busio.UART(tx_pin, rx_pin, baudrate=baud, timeout=0.01)
    print("UART initialized on TX:", config["uart_tx"], "RX:", config["uart_rx"], "at", baud, "bps")

# Initialize UART initially
init_uart()

# Setup USB MIDI endpoints
# usb_midi.ports[0]: Host-to-device (MIDI IN)
# usb_midi.ports[1]: Device-to-host (MIDI OUT)
midi_in = usb_midi.ports[0]
midi_out = usb_midi.ports[1]

def print_help():
    print("Commands:")
    print("  help                  -- show this help message")
    print("  status                -- show current configuration")
    print("  set baud <value>      -- set UART baud rate (e.g., set baud 115200)")
    print("  set tx <pin>          -- set UART TX pin (e.g., set tx GP11)")
    print("  set rx <pin>          -- set UART RX pin (e.g., set rx GP10)")
    print("  reboot                -- reboot the device")
    print("  verbose               -- toggle verbose mode")
    print("  exit                  -- exit the shell")
    
# ---------------------------
# Interactive Shell Functions
# ---------------------------
def process_command(cmd):
    """Parse commands from the shell to inspect and update configuration."""
    parts = cmd.strip().split()
    if len(parts) == 0:
        return

    if parts[0].lower() == "status":
        print("=== STATUS ===")
        print("UART baudrate:", config["uart_baud"])
        print("UART TX pin:", config["uart_tx"])
        print("UART RX pin:", config["uart_rx"])
    elif parts[0].lower() == "set" and len(parts) == 3:
        param = parts[1].lower()
        value = parts[2]
        if param == "baud":
            try:
                config["uart_baud"] = int(value)
                save_config()
                init_uart()
                print("UART baudrate updated to", config["uart_baud"])
            except Exception as e:
                print("Error setting baud rate:", e)
        elif param == "tx":
            config["uart_tx"] = value.upper()
            save_config()
            init_uart()
            print("UART TX pin updated to", config["uart_tx"])
        elif param == "rx":
            config["uart_rx"] = value.upper()
            save_config()
            init_uart()
            print("UART RX pin updated to", config["uart_rx"])
        else:
            print("Unknown parameter. Use 'baud', 'tx', or 'rx'.")
    elif parts[0].lower() == "help":
        print_help()
    elif parts[0].lower() == "reboot":
        print("Rebooting...")
        microcontroller.reset()
    elif parts[0].lower() == "exit":
        print("Exiting shell.")
        raise KeyboardInterrupt
    elif parts[0].lower() == "verbose":
        global verbose
        verbose = not verbose
        print("Verbose mode: ", verbose)
    else:
        print("Unknown command. Type 'help' for a list of commands.")

def interactive_shell():
    """Poll the USB serial for commands."""
    if supervisor.runtime.serial_bytes_available:
        try:
            cmd = input(">>> ")
            process_command(cmd)
        except Exception as e:
            print("Shell error:", e)

# ---------------------------
# Main Loop: MIDI Bridging
# ---------------------------
led_t = time.monotonic()
count_in = [0]
count_out = [0]
count_t = time.monotonic()
while True:
    # Flash the LED to indicate the script is running
    if time.monotonic() - led_t > 0.01:
        led.value = False
        led_t = time.monotonic()

    if time.monotonic() - count_t > 1:
        if verbose:
            #sum the contents of count and divide by its lenght to get the average
            average_in = sum(count_in) / len(count_in)
            average_out = sum(count_out) / len(count_out)
            print("Average MIDI messages per second: IN: ", average_in, " OUT: ", average_out)
        count_in = count_in[1:] + [0]
        count_out = count_out[1:] + [0]
        count_t = time.monotonic()

        # --- Interactive Shell --- only once a second
        interactive_shell()
    
    # --- USB MIDI to UART ---
    usb_data = None
    while True:
        d = midi_in.read(2048)  # read up to 2048 bytes at a time
        if not d:
            break
        if usb_data is None:
            usb_data = d
        else:
            usb_data += d
        if len(usb_data) > 1024:
            break

    # usb_data = midi_in.read(2048)

    if usb_data:
        led.value = True
        uart.write(usb_data)
        # print(len(usb_data))
        count_out[-1] += len(usb_data)
        # led.value = False
        # print("Forwarded USB MIDI to UART:", usb_data)

    # --- UART to USB MIDI ---
    while True:
        uart_data = uart.read(2048)  # read up to 2048 bytes at a time
        if uart_data:
            led.value = True
            midi_out.write(uart_data)
            count_in[-1] += len(uart_data)
            # led.value = False
            # print("Forwarded UART MIDI to USB:", uart_data)
        else:
            break


    # Short sleep to yield processing time and allow background tasks (like USB) to run
    time.sleep(0.000001)

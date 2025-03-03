#!/usr/bin/env python3

import rtmidi

def midi_callback(event, data=None):
    message, _ = event
    print(f"Received MIDI message: {message}")

def main():
    midi_in = rtmidi.MidiIn()
    available_ports = midi_in.get_ports()

    if not available_ports:
        print("No MIDI input ports available.")
        return

    midi_in_ports = []
    for port_name in available_ports:
        mid = rtmidi.MidiIn()
        mid.open_port(available_ports.index(port_name))
        mid.set_callback(midi_callback)
        midi_in_ports.append(mid)
        print(f"Opened MIDI input port: {port_name}")

    print("MIDI logger is active. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

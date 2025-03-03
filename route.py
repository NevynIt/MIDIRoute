#!/usr/bin/env python3
#I need to create a python script to run on linux on a raspberry pi, that will route all the MIDI traffic based on a configuration file
#The configuration file will be a simple text file with the following format:
#<source port> <destination port>

import os
import rtmidi
import re
import time
import threading

received_count = {}
sent_count = {}

def main():
    config_file = "midi_routes.txt"
    midi_in_ports = []
    midi_out_ports = []
    routes = []

    # Check if config file exists, create default if not
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}")
        print("Creating default configuration file...")
        midi_in = rtmidi.MidiIn()
        available_in = midi_in.get_ports()
        midi_out = rtmidi.MidiOut()
        available_out = midi_out.get_ports()

        def parse_port_info(port_str):
            match = re.match(r'^(.*)\s+(\d+:\d+)$', port_str)
            if match:
                name = match.group(1)
                num_id = match.group(2)
                return num_id, name
            else:
                return port_str, port_str

        with open(config_file, "w") as f:
            in_ids, out_ids = [], []

            # Write input port comments
            for port in available_in:
                num_id, name = parse_port_info(port)
                f.write(f"#{num_id} = {name}\n")
                in_ids.append(num_id)
            f.write("#\n")
            # Write output port comments
            for port in available_out:
                num_id, name = parse_port_info(port)
                f.write(f"#{num_id} = {name}\n")
                out_ids.append(num_id)
            f.write("#\n")

            # Write routes using numeric IDs with "->"
            for i_id in in_ids:
                for o_id in out_ids:
                    if i_id == o_id:
                        continue
                    f.write(f"{i_id} -> {o_id}\n")

        print(f"Default configuration file created: {config_file}")
        exit(0)

    # Read routes from config
    with open(config_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            source, dest = re.split(r'\s*->\s*', line)
            routes.append((source, dest))

    # Group routes by source
    source_routes = {}
    for source, dest in routes:
        if source not in source_routes:
            source_routes[source] = []
        source_routes[source].append(dest)

    out_map = {}
    # Gather all distinct destinations
    all_dests = {d for _, ds in source_routes.items() for d in ds}
    for dest in all_dests:
        mo = rtmidi.MidiOut()
        if dest not in mo.get_ports():
            print(f"Opening virtual port for {dest}")
            mo.open_virtual_port(dest)
        else:
            print(f"Opening port for {dest}")
            mo.open_port(mo.get_ports().index(dest))
        out_map[dest] = mo

    def create_midi_callback(source):
        def midi_callback(event, dest_list):
            message, _ = event
            received_count[source] = received_count.get(source, 0) + 1
            print(f"Received on {source}: {message}")
            for d in dest_list:
                out_map[d].send_message(message)
                sent_count[d] = sent_count.get(d, 0) + 1
        return midi_callback

    def print_statistics():
        while True:
            time.sleep(10)
            print("=== MIDI Statistics ===")
            for src, count in received_count.items():
                print(f"Received on {src}: {count}")
                received_count[src] = 0
            for dst, count in sent_count.items():
                print(f"Sent to {dst}: {count}")
                sent_count[dst] = 0

    stats_thread = threading.Thread(target=print_statistics, daemon=True)
    stats_thread.start()

    # Open each source once
    for source, dests in source_routes.items():
        mid = rtmidi.MidiIn()
        in_ports = mid.get_ports()
        if source in in_ports:
            idx = in_ports.index(source)
            print(f"Opening port {source} at index {idx}")
            mid.open_port(idx)
        else:
            print(f"Opening virtual port for {source}")
            mid.open_virtual_port(source)
        mid.set_callback(create_midi_callback(source), dests)
        midi_in_ports.append(mid)

    print("MIDI routing is active. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
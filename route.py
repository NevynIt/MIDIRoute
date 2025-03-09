import os, subprocess, sys
import rtmidi, rtmidi.midiutil
import re
import time

def get_midi_ports():
    api = rtmidi.MidiIn()
    inp = api.get_ports()
    inp = [x for x in inp if "RtMidi" not in x]
    api.delete()
    api = rtmidi.MidiOut()
    outp = api.get_ports()
    outp = [x for x in outp if "RtMidi" not in x]
    api.delete()
    return inp, outp

src_ports = {}
dst_ports = {}
routes = {}
defs = {}
received_count = 0

config_file = "midi_routes.txt"
if not os.path.exists(config_file):
    print(f"Config file {config_file} not found.")
    exit(1)

def midi_callback(event, dest_set):
    global received_count, dst_ports
    message, _ = event
    received_count += 1
    for id in dest_set:
        if id in dst_ports:
            dst_ports[id][0].send_message(message)

re_def = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*(.*)$")
re_route = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_, ]+)\s*$")
with open(config_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re_def.match(line)
        if m:
            id = m.group(1)
            key = m.group(2).strip()
            print(f"Defining {id} as {key}")
            if id in defs:
                print(f"Duplicate definition for {id}, ignoring the second one")
                continue

            defs[id] = key
            routes[id] = set()
        else:
            m = re_route.match(line)
            if m:
                src = m.group(1)
                dst = m.group(2).split(",")
                if src not in defs:
                    print(f"Source {src} not defined, ignoring rule {line}")
                else:
                    for id in dst:
                        id = id.strip()
                        routes[src].add(id)

midi_in_ports, midi_out_ports = get_midi_ports()
print("Opening ports")
for id, key in defs.items():
    print(f"Searching input port '{key}' for {id}")
    try:
        src_ports[id] = rtmidi.midiutil.open_midiinput(key, interactive=False, use_virtual=False)
        print(f"Input port found: {src_ports[id][1]}")
        print("Setting callback")
        src_ports[id][0].set_callback(midi_callback, routes[id])
    except Exception as e:
        print(f"Error opening input port: {e}")

    print(f"Searching output port '{key}' for {id}")
    try:
        dst_ports[id] = rtmidi.midiutil.open_midioutput(key, interactive=False, use_virtual=False)
        print(f"Output port found: {dst_ports[id][1]}")
    except Exception as e:
        print(f"Error opening output port: {e}")

output = subprocess.check_output("aconnect -l", shell=True).decode()

print("MIDI routing is active. Press Ctrl+C to stop.")
try:
    last_check = 0
    interval = 5
    while True:
        if time.time() - last_check > interval:
            print(f"{received_count/(time.time() - last_check)} msg/s")
            last_check = time.time()
            received_count = 0

            new_output = subprocess.check_output("aconnect -l", shell=True).decode()
            if new_output != output:
                print("aconnect output changed, restarting")
                os.execl(sys.executable, sys.executable, *sys.argv)
            # try:
            #     new_in_ports, new_out_ports = get_midi_ports()
            # except Exception as e:
            #     print(f"Error getting MIDI ports: {e}")
            #     new_in_ports, new_out_ports = midi_in_ports, midi_out_ports
            # if ",".join(new_in_ports) != ",".join(midi_in_ports) or ",".join(new_out_ports) != ",".join(midi_out_ports):
            #     print("MIDI device change detected, restarting")
            #     os.execl(sys.executable, sys.executable, *sys.argv)
                # print(f"Old input ports: {repr(midi_in_ports)}")
                # print(f"New input ports: {repr(new_in_ports)}")
                # print(f"Old output ports: {repr(midi_out_ports)}")
                # print(f"New output ports: {repr(new_out_ports)}")
                # #close all ports
                # print("Closing all ports")
                # for source in src_ports.values():
                #     source[0].close_port()
                #     del source[0]
                # src_ports.clear()
                # for dest in dst_ports.values():
                #     dest[0].close_port()
                #     del dest[0]
                # dst_ports.clear()

                # midi_in_ports, midi_out_ports = new_in_ports, new_out_ports
                # #open all valid ports
                # print("Reopening ports")
                # for id, key in defs.items():
                #     print(f"Searching input port '{key}' for {id}")
                #     try:
                #         src_ports[id] = rtmidi.midiutil.open_midiinput(key, interactive=False, use_virtual=False)
                #         print(f"Input port found: {src_ports[id][1]}")
                #         print("Setting callback")
                #         src_ports[id][0].set_callback(midi_callback, routes[id])
                #     except Exception as e:
                #         print(f"Error opening input port: {e}")

                #     print(f"Searching output port '{key}' for {id}")
                #     try:
                #         dst_ports[id] = rtmidi.midiutil.open_midioutput(key, interactive=False, use_virtual=False)
                #         print(f"Output port found: {dst_ports[id][1]}")
                #     except Exception as e:
                #         print(f"Error opening output port: {e}")
        time.sleep(0.1)

except KeyboardInterrupt:
    pass
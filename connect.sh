#!/bin/bash

# client 0: 'System' [type=kernel]
#     0 'Timer           '
#     1 'Announce        '
# client 14: 'Midi Through' [type=kernel]
#     0 'Midi Through Port-0'
# client 20: 'APC Key 25 mk2' [type=kernel,card=1]
#     0 'APC Key 25 mk2 APC Key 25 mk2 K'
#     1 'APC Key 25 mk2 APC Key 25 mk2 C'
# client 24: 'USB MIDI Interface' [type=kernel,card=2]
#     0 'USB MIDI Interface MIDI 1'
# client 28: 'Arturia MicroFreak' [type=kernel,card=3]
#     0 'Arturia MicroFreak Arturia Micr'
#         Connected From: 32:0
# client 32: 'Circuit Tracks' [type=kernel,card=4]
#     0 'Circuit Tracks MIDI'
#         Connecting To: 28:0

P85="USB MIDI Interface"
TRACKS="Circuit Tracks"
UFREAK="Arturia MicroFreak"
APC25="APC Key 25 mk2"

while true; do
    #connect all midi ports

    #p85 to microfreak and tracks
    aconnect "$P85" "$UFREAK"
    aconnect "$P85" "$TRACKS"

    #tracks to microfreak and p85
    aconnect "$TRACKS" "$UFREAK"
    aconnect "$TRACKS" "$P85"

    #apc25 to tracks
    aconnect "$APC25" "$TRACKS"

    #microfreak to tracks
    aconnect "$UFREAK" "$TRACKS"

    # Sleep for 5 seconds
    sleep 5
done
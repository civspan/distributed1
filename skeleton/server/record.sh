#!/bin/sh
# FFmppeg Linux screen recorder
#
REC_iface=$(pactl list sources short | awk '{print$2}' | grep 'monitor')
SCREEN_res=$(xrandr -q --current | grep '*' | awk '{print$1}')

ffmpeg -f alsa -i hw:1 pulse -i $REC_iface -ac 2 -acodec vorbis -f x11grab -r 25 -s $SCREEN_res -i :0.0 -vcodec libx264 output.mkv

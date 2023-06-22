#!/bin/bash
#title           :get_usb.bash
#description     :Find the USB-to-RS232C Adaptor
#author          :Nicholas Putra Rihandoko
#date            :2023/05/12
#version         :0.1
#usage           :Modbus programming in Python
#notes           :
#==============================================================================


# Find the line with specific USB name
line=$(ls -l /dev/serial/by-id | grep 'Prolific_Technology_Inc')

# Extract the 'ttyUSB5' part from the line
path=$(echo "$line" | awk '{print $NF}')

# Check if the device name was found
if [ -n "$path" ]; then
filename=$(basename "$path")
device_name="${filename%.*}"
echo "/dev/$device_name"
else
echo ""
fi
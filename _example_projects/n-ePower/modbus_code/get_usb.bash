#!/bin/bash
#title           :get_usb.bash
#description     :Find the USB device directory
#author          :Nicholas Putra Rihandoko
#date            :2023/07/19
#version         :0.1
#usage           :programming in Python
#notes           :
#==============================================================================


# Find the line with specific USB name
id=$1
line=$(ls -l /dev/serial/by-id | grep "$id")

# Extract the 'ttyUSB*' part from the line
path=$(echo "$line" | awk '{print $NF}')

# Check if the device name was found
if [ -n "$path" ]; then
filename=$(basename "$path")
device_name="${filename%.*}"
echo "/dev/$device_name"
else
echo $id
fi
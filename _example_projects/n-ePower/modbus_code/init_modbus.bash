#!/bin/bash
#title           :init_modbus.bash
#description     :CAN Hat module installation script
#author          :Nicholas Putra Rihandoko
#date            :2023/06/21
#version         :2.1
#usage           :Modbus programming in Python
#notes           :
#==============================================================================

# Enable UART for communication with the RS485 Hat
sed -i 's/^enable_uart=0/enable_uart=1/g' /boot/config.txt
sed -i 's/^#enable_uart=0/enable_uart=1/' /boot/config.txt
sed -i 's/^#enable_uart=1/enable_uart=1/' /boot/config.txt
# If the previous lines does not exist yet, add it in /boot/config.txt
if ! sudo grep -q "enable_uart=1" /boot/config.txt; then
    sudo sed -i '4i enable_uart=1' /boot/config.txt
fi
# Use /dev/ttyAMA0 instead of /dev/ttyS0 to solve odd/even parity bit problem
if ! sudo grep -q "dtoverlay=disable-bt" /boot/config.txt; then
    sudo sed -i '4i dtoverlay=disable-bt' /boot/config.txt
fi
# Enable SPI and Serial port
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_serial 0
# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' /boot/config.txt

# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/modbus_code/main__modbus.py
sudo chmod 777 /home/$(logname)/modbus_code/save/modbus_log.csv
sleep 1
# Install pip for python library manager
sudo apt install python3-pip
sleep 1
# Install the necessary python library
sudo pip3 install pymodbus
sudo pip3 install pymysql
sleep 1

echo ""
echo "=========================================================="
echo ""
echo "Installation of Modbus system is finished"
echo ""
echo "Make sure to DISABLE SERIAL CONSOLE through \"sudo raspi-config\" then REBOOT"
echo ""
echo "=========================================================="
echo ""
exit 0
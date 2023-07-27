#!/bin/bash
#title           :init_modbus.bash
#description     :CAN/RS485 Hat module installation script
#author          :Nicholas Putra Rihandoko
#date            :2023/07/19
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
# Enable SPI
sudo raspi-config nonint do_spi 0
# Disable Serial Port to disable Serial Console, then enable Serial port without Serial Console
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint do_serial 2
# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' /boot/config.txt
# ssh and VNC for remote access
sudo systemctl enable ssh
sudo systemctl start ssh
sudo raspi-config nonint do_vnc 0

# Install pip for python library manager
sudo apt update
sudo apt install python3-pip
# Install the necessary python library
sudo pip3 install pymodbus
sudo pip3 install pymysql
# 'zerotier' for virtual LAN and remote access
sudo apt install curl nmap -y
curl -s https://install.zerotier.com | sudo bash
# cron for task automation
sudo apt install cron -y
sudo systemctl enable cron

# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/modbus_code/main__modbus.py
sudo chmod 777 /home/$(logname)/modbus_code/save/modbus_log.csv

echo ""
echo "=========================================================="
echo ""
echo "Installation of Modbus system is finished"
echo ""
echo "Please reboot the RaspberryPi, just in case :)"
echo ""
echo "=========================================================="
echo ""
exit 0
#!/bin/bash

# make sure to:
# ENABLE SPI
# ENABLE SERIAL PORT
# DISABLE SHELL & KERNEL OVER SERIAL CONSOLE
# through raspi-congig

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
# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' /boot/config.txt

# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/modbus_code/modbus_client.py
sudo chmod +x /etc/crontab
# Install pip for python library manager
sudo apt install python3-pip
sleep 1
# Install the necessary python library
sudo pip3 install pymodbus
sudo pip3 install pymysql
sleep 1

# install and enable Cron to automate task
#sudo apt install cron
#sudo systemctl enable cron
# Check whether the command line is already exist in /etc/crontab
#if ! sudo grep -q "@reboot root sleep 10 && sudo python3 /home/$(logname)/modbus_code/modbus_client.py &" /etc/crontab; then
    # Append the file into /etc/crontab to enable automatic run after reboot
#    sudo su -c "echo \"@reboot root sleep 10 && sudo python3 /home/$(logname)/modbus_code/modbus_client.py &\" >> /etc/crontab"
#fi
#sleep 1
# Restart cron service
#sudo service cron restart && sudo systemctl restart cron
sleep 1
echo "Installation of Modbus system is finished"
exit
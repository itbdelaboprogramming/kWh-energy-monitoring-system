#!/bin/sh

# Enable UART for communication with the RS485 Hat
sed -i 's/^enable_uart=0/enable_uart=1/g' /boot/config.txt
sed -i 's/^#enable_uart=0/enable_uart=1/' /path/to/file.txt
sed -i 's/^#enable_uart=1/enable_uart=1/' /path/to/file.txt
# If the previous lines does not exist yet, add it in /boot/config.txt
if ! sudo grep -q "enable_uart=1" /boot/config.txt; then
    sudo echo "enable_uart=1" >> /boot/config.txt
fi
# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' myfile.txt

# Enable execute (run program) privilege for the python script
sudo chmod +x /home/$(logname)/modbusPowerMeter_code/modbusPowerMeter.py
# Install pip for python library manager
sudo apt install python3-pip
sleep 1
# Install the necessary python library
sudo pip3 install pymodbus
sudo pip3 install pymysql
sleep 1

# install and enable Cron to automate task
sudo apt install cron
sudo systemctl enable cron
# Check whether the command line is already exist in /etc/crontab
if ! sudo grep -q "@reboot root sleep 5 && sudo sh /home/$(logname)/modbusPowerMeter_code/modbusPowerMeter.py &" /etc/crontab; then
    # Append the file into /etc/crontab to enable automatic run after reboot
    sudo su -c "echo \"@reboot root sleep 5 && sudo sh /home/$(logname)/modbusPowerMeter_code/modbusPowerMeter.py &\" >> /etc/crontab"
fi
sleep 1
# Enable execute (run program) privilege /etc/rc.local
sudo chmod +x /etc/rc.local
sleep 1
echo "Installation of modbusPowerMeter system is finished"
echo "Please reboot the RaspberryPi"
exit
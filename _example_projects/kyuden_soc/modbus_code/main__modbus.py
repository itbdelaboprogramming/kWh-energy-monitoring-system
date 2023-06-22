"""
#title           :main__modbus.py
#description     :modbus Communication between YASKAWA D1000, YASKAWA GA500, Kyuden Battery 72 kWh, and Raspberry Pi + RS485/CAN Hat + USB-o-RS232C Adaptor
#author          :Nicholas Putra Rihandoko
#date            :2023/05/08
#version         :0.1
#usage           :Energy Monitoring System, RS-485 and RS-232C interface
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

# Import library
import debug
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import datetime # RTC Real Time Clock
import time
import pymysql
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))
import kyuden_battery_72kWh as battery
import yaskawa_D1000 as converter
import yaskawa2_GA500 as inverter
#import tristar_MPPT as charger

# Define Modbus communication parameters
port            = '/dev/ttyAMA0'
port0           = os.popen('bash {}/get_usb.bash'.format(os.path.dirname(os.path.abspath(__file__)))).read().strip()
method          = 'rtu'
bytesize        = 8
stopbits        = 1
parity          = 'N'
baudrate        = 9600   # data/byte transmission speed (in bytes per second)
client_latency  = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout         = 1   # the maximum time the master/client will wait for response from slave/server (in seconds)
com_delay       = 30   # the period between each subsequent communication routine/loop (in seconds)

# Define MySQL Database parameters
mysql_host      = '10.4.171.204'
mysql_db        = 'test'
mysql_user      = 'pi'
mysql_password  = 'raspberrypi'
update_delay    = 300   # the period between each subsequent update to database (in seconds)

# Monitor Modbus communication for debugging
#debug.debugging()
cpu_temp = None     # RaspberryPi temperature for hardware fault monitoring
init = [True,True]  # variable to check modbus & mysql initialization

def setup_modbus():
    global port, port0, method, bytesize, stopbits, parity, baudrate, client_latency, timeout
    # Set each Modbus communication port specification
    client = ModbusClient(port=port, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client0 = ModbusClient(port=port0, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    # Connect to the Modbus serial
    client.connect()
    client0.connect()
    # Define the Modbus slave/server (nodes) objects
    bat = battery.node(unit=1, name='BATTERY', client=client0, delay=client_latency)
    conv = converter.node(unit=2, name='CONVERTER', client=client, delay=client_latency)
    inv = inverter.node(unit=3, name='INVERTER', client=client, delay=client_latency)
    #chr = charger.node(unit=1, name='SOLAR CHARGER', client=client, delay=client_latency)
    server = [bat, conv, inv]
    return server

# Checking the connection Modbus
while init[0]:
    try:
        # Setup Raspberry Pi as Modbus client/master
        server = setup_modbus()
        print("<===== Connected to Modbus Communication =====>")
        print("")
        init[0] = False

    except BaseException as e:
        # Print the error message
        print("problem with Modbus communication:")
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

# Checking the connection MySQL
while init[1]:
    try:
        # Setup Raspberry Pi as Database client
        db = pymysql.connect(host=mysql_host, user=mysql_user, password=mysql_password, db=mysql_db, port=3306)
        print("<===== Connected to MySQl Server =====>")
        print("")
        init[1] = False

    except BaseException as e:
        # Print the error message
        print("problem with MySQL Server:")
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

first = [True, True]
# Reading a Modbus message and Upload to database sequence
while not init[0] and not init[1]:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            # time counter
            start = datetime.datetime.now()
            # Reset accumulated values for first time measurements
            for i in range(len(server)):
                server[i].reset_read_attr()
            debug.log_in_csv(server, cpu_temp, start, first_row=True)
            
        # Send the command to read the measured value
        for i in range(len(server)):
            try:
                server[i].send_command(command="read_measurement")
            except BaseException as e:
                # Reset the value of measurement
                server[i].reset_read_attr()
                # Print the error message
                print("problem with",server[i]._name,":")
                print(e)
                print("<===== ===== continuing ===== =====>")
                print("")

        # Save and print the data
        timer = datetime.datetime.now()
        cpu_temp = debug.get_cpu_temperature()
        debug.log_in_csv(server, cpu_temp, timer)
        debug.print_response(server, cpu_temp, timer)
        
        # Check elapsed time
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            debug.update_database(server, db, cpu_temp, timer)
        
        time.sleep(com_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(1)

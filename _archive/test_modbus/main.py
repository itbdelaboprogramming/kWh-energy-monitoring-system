"""
#title           :main.py
#description     :modbus Communication between Omron KM-N1-FLK and Raspberry Pi + RS485/CAN Hat
#author          :Fajar Muhammad Noor Rozaqi, Nicholas Putra Rihandoko
#date            :2023/04/07
#version         :1.1
#usage           :Energy Monitoring System
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
import omron_KMN1FLK as omron
import os

# Monitor Modbus communication for debugging
#debug.debugging()

# Define Modbus communication parameters
port            = "/dev/ttyAMA0"
method          = 'rtu'
bytesize        = 8
stopbits        = 1
parity          = 'E'
baudrate        = 9600   # data/byte transmission speed (in bytes per second)
client_latency  = 200   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout         = 5   # the maximum time the master/client will wait for response from slave/server (in seconds)
com_delay       = 5   # the period between each subsequent communication routine/loop (in seconds)

# Define MySQL Database parameters
mysql_host      = '****'
mysql_db        = '****'
mysql_user      = '****'
mysql_password  = '****'
update_delay    = 300   # the period between each subsequent update to database (in seconds)

cpu_temp = None     # RaspberryPi temperature for hardware fault monitoring
init = [True,True]  # variable to check modbus & mysql initialization

def setup_modbus():
    global port, method, bytesize, stopbits, parity, baudrate, client_latency, timeout
    # Set each Modbus communication port specification
    client = ModbusClient(port=port, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    # Connect to the Modbus serial
    client.connect()
    # Define the Modbus slave/server (nodes) aobjects
    ct2 = omron.node(unit=2, name='OMRON', client=client, delay=client_latency)
    ct3 = omron.node(unit=3, name='OMRON', client=client, delay=client_latency)
    server = [ct2, ct3]
    # Set server latency
    server[0].send_command(command="Shift_to_Setting")
    server[0].send_command(command="set_Server_Transmission_Delay",param=50)    # (in milliseconds)
    server[0].send_command(command="Shift_to_Measurement")
    return server

def update_database(server,db,cpu_temp,timer):
    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `test`"
                "(DateTime, RPi_Temp) "
                "VALUES (%s,%s)")
    try:
        # Write data in database
        db.cursor().execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),cpu_temp))
        db.commit()
        print("<===== Data is sent to database =====>")
        print("")
    except BaseException as e:
        # Print the error message
        print("Cannot update MySQl database")
        print("problem with -->",e)
        print("<===== ===== continuing ===== =====>")
        print("")

def get_cpu_temperature():
    # Read CPU temperature from file
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp = round(float(f.read().strip())/1000,1)
    return temp

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
        db = pymysql.connect(host=mysql_host, user=mysql_user, password=mysql_password, db=mysql_db)
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

# time counter
start = datetime.datetime.now()
first = [True, True]
# Reset accumulated values for first time measurements
for i in range(len(server)):
    server[i].reset_read_attr()

# Reading a Modbus message and Upload to database sequence
while not init[0] and not init[1]:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            
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

        # Print the data
        timer = datetime.datetime.now()
        cpu_temp = get_cpu_temperature()
        debug.print_response(server, cpu_temp, timer)
        
        # Check elapsed time
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            update_database(server, db, cpu_temp, timer)
        
        time.sleep(com_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(1)

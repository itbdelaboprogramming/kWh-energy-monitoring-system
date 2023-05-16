"""
#title           :modbusPowerMeter.py
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
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import datetime # RTC Real Time Clock
import time
import pymysql
import omron_KMN1FLK as omron

#time.sleep(10)     # wait for RaspberryPi to complete its boot-up sequence
cpu_temp = None     # RaspberryPi temperature for hardware fault monitoring
init = [True,True]  # variable to check modbus & mysql initialization

# Define communication parameters
port = "/dev/ttyAMA0"
method = 'rtu'
bytesize = 8
stopbits = 1
parity = 'E'
baudrate = 9600   # data/byte transmission speed (in bytes per second)
server_latency = 50   # the delay time slave/server takes from completing command/request to sending the response (in milliseconds)
client_latency = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout = 5   # the maximum time the master/client will wait for response from slave/server (in seconds)
measure_delay = 2   # the period between each subsequent measurement (in seconds)
update_delay = 300   # the period between each subsequent update to database (in seconds)

# Define the Modbus's slave/server (nodes) and the master/client transmission waiting time
ct2 = omron.node(unit=2, delay=client_latency)

def print_response(server, name):
    global cpu_temp
    # Uncomment as needed
    print(name, "MEASUREMENTS")
    print("Time             :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
    print("CPU Temperature  :", cpu_temp, "degC")
    for attr_name, attr_value in vars(server).items():
        if not isinstance(attr_value, list):
            if "SOC" in attr_name:
                print(attr_name, "=", attr_value, "%")
            elif "Frequency" in attr_name:
                print(attr_name, "=", attr_value, "Hz")
            elif "Voltage" in attr_name:
                print(attr_name, "=", attr_value, "Volts")
            elif "Current" in attr_name:
                print(attr_name, "=", attr_value, "Amps")
            elif "Power" in attr_name:
                print(attr_name, "=", attr_value)
            elif "Energy" in attr_name:
                print(attr_name, "=", attr_value)
            elif "Temperature" in attr_name:
                print(attr_name, "=", attr_value, "degC")
    print("")

def update_database(server):
    global cpu_temp, db, cur
    num = len(server)
    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `test`"
                "(DateTime, RPi_Temp) "
                "VALUES (%s,%s)")

    # Write data in database
    cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),cpu_temp))
    db.commit()
    print("Data is sent to database")
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
        client = ModbusClient(method=method, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
        client.connect()
        print("Connected to Modbus Communication")
        print("")
        init[0] = False

    except BaseException as e:
        # Print the error message
        print("Cannot find Modbus Communication")
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)
        pass

# Checking the connection MySQL
while init[1]:
    try:
        # Setup Raspberry Pi as Database client
        db = pymysql.connect(host='192.168.200.93',
                             #port=*****,
                             user='pi',   # MySQL user
                             password='raspberrypi',   # MySQL password
                             db='test')   # MySQL database
        cur = db.cursor()
        print("Connected to MySQl Server")
        print("")
        init[1] = False

    except BaseException as e:
        # Print the error message
        print("Cannot access MySQl Server")
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)
        pass

# time counter
start = datetime.datetime.now()
first = [True, True]

# Reading a Modbus Message
while True:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            # Reset accumulated values for first time measurements
            
        # Send the command to read the measured value
        ct2.send_command(client=client, command="read_measurement")
        cpu_temp = get_cpu_temperature()

        # Print the data
        timer = datetime.datetime.now()
        print_response(ct2, "OMRON CT2")

        # Check elapsed time
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            update_database([ct2])
        
        time.sleep(measure_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(5)
        pass

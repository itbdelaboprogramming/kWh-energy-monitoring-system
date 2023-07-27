"""
#title           :main__modbus.py
#description     :modbus Communication between Modbus devices and Raspberry Pi + RS485/CAN Hat + USB-to-RS232C Adaptor
#author          :Nicholas Putra Rihandoko
#date            :2023/07/19
#version         :1.0
#usage           :Energy Monitoring System, RS-485 and RS-232C interface
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

# Import library
import query
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import datetime # RTC Real Time Clock
import time
from lib import omron_KMN1FLK as omron
from lib import msystem_M5XWTU113 as msystem
from lib import electricPowerCalc as calc

# Define Modbus communication parameters
port            = '/dev/ttyAMA0'    # for RS485/CAN Hat
method          = 'rtu'
bytesize        = 8
stopbits        = 1
parity          = 'E'
baudrate        = 9600   # data/byte transmission speed (in bytes per second)
client_latency  = 300   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout         = 1   # the maximum time the master/client will wait for response from slave/server (in seconds)
interval        = 1   # the period between each subsequent communication routine/loop (in seconds)

# Define MySQL Database parameters
mysql_server    = {"host":"10.4.171.204",
                    "user":"pi",
                    "password":"raspberrypi",
                    "db":"test",
                    "table":"test",
                    "port":3306}
mysql_timeout   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
mysql_interval  = 300 # the period between each subsequent update to database (in seconds)

#query.debugging()  # Monitor Modbus communication for debugging
init = True  # variable to check Modbus initialization

def setup_modbus():
    global port, method, bytesize, stopbits, parity, baudrate, client_latency, timeout
    # Set each Modbus communication port specification
    client = ModbusClient(port=port, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    # Connect to the Modbus serial
    client.connect()
    # Define the Modbus slave/server (nodes) objects
    ct1 = omron.node(unit=3, name='OMRON CT1', client=client, delay=client_latency, max_count=20, increment=2, shift=0)
    ct2 = omron.node(unit=2, name='OMRON CT2', client=client, delay=client_latency, max_count=20, increment=2, shift=0)
    ct3 = omron.node(unit=1, name='MSYSTEM', client=client, delay=client_latency, max_count=20, increment=2, shift=2)
    server = [ct1,ct2,ct3]
    return server

def read_modbus(server):
    #return
    addr=[["Voltage_1",0x0208],
            [0x0000],
            ["voltage"]]
    for i in range(len(server)):
        try:
            pass
            server[i].send_command(command="read",address=addr[i])
            #print(server[i].map_read_attr([0x0000,0x000E,0x0208]))
        except Exception as e:
            # Print the error message
            print("problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_modbus(server):
    #return
    for i in range(len(server)):
        try:
            pass
            #server[i].send_command(command="write",address="shift_to_setting") # go to settings
            #server[i].send_command(command="write",address=0x2608,param=69)
            #server[i].send_command(command="write",address=0xFFFF,param=0x0400) # go to measurements
        except Exception as e:
            # Print the error message
            print("problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def update_database(server, timer):
    global mysql_server
    # Define MySQL queries and data which will be used in the program
    cpu_temp = query.get_cpu_temperature()
    [bootup_time, uptime, total_uptime, downtime, total_downtime] = query.get_updown_time(mysql_server, timer, mysql_timeout)
    title = ["RPi_Temp","Volt1","Volt2",
                "startup_date","startup_time","uptime","total_uptime",
                "shutdown_date","shutdown_time","downtime","total_downtime"]
    mysql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(mysql_server["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))
    data = [cpu_temp, server[0].Voltage_1, server[1].Voltage_1,
                bootup_time.strftime("%Y-%m-%d"), bootup_time.strftime("%H:%M:%S"), uptime, total_uptime,
                timer.strftime("%Y-%m-%d"), timer.strftime("%H:%M:%S"), downtime, total_downtime]
    filename = 'modbus_log.csv'

    query.log_in_csv(title ,data, timer, filename)
    query.retry_mysql(mysql_server, mysql_query, filename, mysql_timeout)

#################################################################################################################

# Checking the connection Modbus
while init:
    try:
        # Setup Raspberry Pi as Modbus client/master
        server = setup_modbus()
        print("<===== Connected to Modbus Communication =====>")
        print("")
        init = False
    except Exception as e:
        # Print the error message
        print("problem with Modbus communication:")
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

first = [True, True]
# Reading a Modbus message and Upload to database sequence
while not init:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            start = datetime.datetime.now() # time counter
            write_modbus(server)
            
        # Send the command to read the measured value and do all other things
        timer = datetime.datetime.now()
        read_modbus(server)
        query.print_response(server, timer)
        
        # Check elapsed time
        if (timer - start).total_seconds() > mysql_interval or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            update_database(server, timer)
        
        time.sleep(interval)
    
    except Exception as e:
        # Print the error message
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

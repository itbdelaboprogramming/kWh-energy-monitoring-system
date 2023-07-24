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
import os
from lib import kyuden_battery_72kWh as battery
from lib import yaskawa_D1000 as converter
from lib import yaskawa_GA500 as inverter

# Define Modbus communication parameters
port            = '/dev/ttyAMA0'    # for RS485/CAN Hat
port_id0        = 'Prolific_Technology_Inc' # for USB-to-RS232C adaptor
port0           = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), port_id0)).read().strip()
method          = 'rtu'
bytesize        = 8
stopbits        = 1
parity          = 'N'
baudrate        = 9600   # data/byte transmission speed (in bytes per second)
client_latency  = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout         = 1   # the maximum time the master/client will wait for response from slave/server (in seconds)
interval        = 30   # the period between each subsequent communication routine/loop (in seconds)

# Define MySQL Database parameters
mysql_server    = {"host":"10.4.171.204",
                    "user":"pi",
                    "password":"raspberrypi",
                    "db":"test",
                    "table":"kyuden_soc",
                    "port":3306}
mysql_timeout   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
mysql_interval  = 300 # the period between each subsequent update to database (in seconds)

#query.debugging()  # Monitor Modbus communication for debugging
init = True  # variable to check Modbus initialization
bootup_time = datetime.datetime.now()   # Used to gat the startup timestamp of the script
timer = bootup_time

def setup_modbus():
    global port, port0, method, bytesize, stopbits, parity, baudrate, client_latency, timeout
    # Set each Modbus communication port specification
    client = ModbusClient(port=port, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client0 = ModbusClient(port=port0, method=method, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    # Connect to the Modbus serial
    client.connect()
    client0.connect()
    # Define the Modbus slave/server (nodes) objects
    bat = battery.node(unit=1, name='BATTERY', client=client0, delay=client_latency, max_count=20, increment=1, shift=0)
    conv = converter.node(unit=2, name='CONVERTER', client=client, delay=client_latency, max_count=20, increment=1, shift=0)
    inv = inverter.node(unit=3, name='INVERTER', client=client, delay=client_latency, max_count=20, increment=1, shift=0)
    server = [bat, conv, inv]
    return server

def read_modbus(server):
    #return
    addr=[["Cell_Voltage_M1","Cell_Voltage_M2","Cell_Voltage_M3","Cell_Voltage_M4","Cell_Voltage_M5","Cell_Voltage_M6","Cell_Voltage_M7","Cell_Voltage_M8",
           "Cell_Voltage_M9","Cell_Voltage_M10","Cell_Voltage_M11","Cell_Voltage_M12","Cell_Voltage_M13","Cell_Voltage_M14","Cell_Voltage_M15","Cell_Voltage_M16",
           "Module_Temperature", "SOC","Total_Voltage"],
            ["DC_Current"],["DC_Current","AC_Power"]]
    for i in range(len(server)):
        try:
            server[i].send_command(command="read",address=addr[i])
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
        except Exception as e:
            # Print the error message
            print("problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def update_database(server):
    global mysql_server, timer, bootup_time
    # Define MySQL queries and data which will be used in the program
    cpu_temp = query.get_cpu_temperature()
    title = ["DateTime","RPi_Temp", "Bat_Temp", "SoC", "Bat_Volt_Total"
                "Bat_Volt_M1", "Bat_Volt_M2", "Bat_Volt_M3", "Bat_Volt_M4",
                "Bat_Volt_M5", "Bat_Volt_M6", "Bat_Volt_M7", "Bat_Volt_M8",
                "Bat_Volt_M9", "Bat_Volt_M10", "Bat_Volt_M11", "Bat_Volt_M12",
                "Bat_Volt_M13", "Bat_Volt_M14", "Bat_Volt_M15", "Bat_Volt_M16",
                "Conv_Chrg_Amps", "new_Inv_Dchrg_Amps", "new_Inv_OutAC_kW"]
    mysql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(mysql_server["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))
    data = [timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp, query.strval(query.mtemp(server[0].Module_Temperature)), server[0].SOC, server[0].Total_Voltage,
                query.strval(server[0].Cell_Voltage_M1), query.strval(server[0].Cell_Voltage_M2), query.strval(server[0].Cell_Voltage_M3), query.strval(server[0].Cell_Voltage_M4),
                query.strval(server[0].Cell_Voltage_M5), query.strval(server[0].Cell_Voltage_M6), query.strval(server[0].Cell_Voltage_M7), query.strval(server[0].Cell_Voltage_M8),
                query.strval(server[0].Cell_Voltage_M9), query.strval(server[0].Cell_Voltage_M10), query.strval(server[0].Cell_Voltage_M11), query.strval(server[0].Cell_Voltage_M12),
                query.strval(server[0].Cell_Voltage_M13), query.strval(server[0].Cell_Voltage_M14), query.strval(server[0].Cell_Voltage_M15), query.strval(server[0].Cell_Voltage_M16),
                server[1].DC_Current, server[2].DC_Current, server[2].AC_Power]
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
            # time counter
            start = datetime.datetime.now()
            write_modbus(server)
            
        # Send the command to read the measured value and do all other things
        read_modbus(server)
        timer = datetime.datetime.now()
        query.print_response(server, timer)

        # Check elapsed time
        if (timer - start).total_seconds() > mysql_interval or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            update_database(server)
        
        time.sleep(interval)
    
    except Exception as e:
        # Print the error message
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

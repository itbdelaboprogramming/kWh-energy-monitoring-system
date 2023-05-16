"""
#title           :main.py
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
import kyuden_battery_72kWh as battery
import yaskawa_D1000 as converter
import yaskawa_GA500 as inverter
import tristar_MPPT as charger
import os

# Monitor Modbus communication for debugging
#debug.debugging()

# Define Modbus communication parameters
port            = '/dev/ttyAMA0'
port0           = os.popen('bash {}/check_usb.bash'.format(os.path.dirname(os.path.abspath(__file__)))).read().strip()
method          = 'rtu'
bytesize        = 8
stopbits        = 1
parity          = 'N'
baudrate        = 9600   # data/byte transmission speed (in bytes per second)
client_latency  = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout         = 5   # the maximum time the master/client will wait for response from slave/server (in seconds)
measure_delay   = 5   # the period between each subsequent measurement (in seconds)

# Define MySQL Database parameters
mysql_host      = '****'
mysql_db        = '****'
mysql_user      = '****'
mysql_password  = '****'
update_delay    = 300   # the period between each subsequent update to database (in seconds)

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
    bat = battery.node(unit=1, name='BATTERY', client=client, delay=client_latency)
    conv = converter.node(unit=2, name='CONVERTER', client=client, delay=client_latency)
    inv = inverter.node(unit=3, name='INVERTER', client=client, delay=client_latency)
    chr = charger.node(unit=4, name='SOLAR CHARGER', client=client, delay=client_latency)
    server = [bat, conv, inv]
    return server


def update_database(server,db,cpu_temp,timer):
    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `dataparameter`"
                "(dc_bus_v_ref, power_supply_vol, power_supply_current, "
                "dc_bus_side_power, power_supply_freq, power_factor, "
                "electric_power_kwh, regene_power_kwh, out_freq, "
                "out_current, out_vol_ref, out_power, "
                "soc, total_vol, cell_avg_vol, "
                "avg_temp, dataentered, CPU_temp, "
                "power_supply_side_power) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    try:
        # Write data in database
        db.cursor().execute(add_c1,
                (server[1].DC_Voltage_command, server[1].AC_Voltage, server[1].AC_Current,
                server[1].DC_Power_kW, server[1].AC_Frequency, server[1].Power_Factor,
                server[1].Consumed_Energy_kWh, server[1].Consumed_Energy_kWh, server[2].Output_Frequency,
                server[2].Output_Current, server[2].Output_Voltage_ref, server[2].Output_Power_kW,
                server[0].SOC, server[0].Total_Voltage, server[0].Cell_Voltage_avg,
                server[0].Temperature_avg, timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp,
                server[1].AC_Power_kW))
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

# Reading a Modbus message and Upload to database sequence
while not init[0] and not init[1]:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            # Reset accumulated values for first time measurements
            for i in range(len(server)):
                server[i].reset_read_attr()
            
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
        
        time.sleep(measure_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(5)

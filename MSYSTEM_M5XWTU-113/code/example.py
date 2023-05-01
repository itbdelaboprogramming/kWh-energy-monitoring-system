"""
#title           :modbusPowerMeter.py
#description     :modbus Communication between MSYSTEM M5XWTU-113 and Raspberry Pi + RS485/CAN Hat
#author          :Nicholas Putra Rihandoko
#date            :2023/04/07
#version         :0.1
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
import msystem_M5XWTU113 as msystem
import os

#time.sleep(10)     # wait for RaspberryPi to complete its boot-up sequence
cpu_temp = None     # RaspberryPi temperature for hardware fault monitoring

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
measure_delay = 3   # the period between each subsequent measurement (in seconds)
update_delay = 6   # the period between each subsequent update to database (in seconds)

# Define the Modbus's slave/server (nodes) and the master/client transmission waiting time
ct1 = msystem.node(unit=1, delay=client_latency)

# Initiate measurement variable for custom value calculation
Voltage = []
Current = []
PowerFactor = []
ActivePowerW = []
ReactivePowerVAr = []

def get_cpu_temperature():
    # Read CPU temperature from file
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp = round(float(f.read().strip())/1000,1)
    return temp

def print_response(ct):
    global cpu_temp
    # Uncomment as needed
    print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
    print("CPU Temperature        :", cpu_temp, "degC")
    print("Voltage                :", ct.Voltage,"V")
    print("Current                :", ct.Current,"A")
    print("Power Factor           :", ct.PowerFactor)
    print("Frequency              :", ct.Frequency,"Hz")
    print("Active Power           :", ct.ActivePowerW,"Watt")
    print("Reactive Power         :", ct.ReactivePowerVAr,"VAr")
    #print("Consumed Energy        :", ct.ConsumedEnergyWh,"Wh")
    #print("Generated Energy       :", ct.GeneratedEnergyWh,"Wh")
    #print("Leading Reactive Energy:", ct.LeadReactiveEnergyVArh,"VArh")
    #print("Lagging Reactive Energy:", ct.LagReactiveEnergyVArh,"VArh")
    print("Total Reactive Energy  :", ct.TotalReactiveEnergyVArh,"VArh")
    print("Consumed Energy        :", ct.ConsumedEnergyKWh,"kWh")
    print("Generated Energy       :", ct.GeneratedEnergyKWh,"kWh")
    #print("Leading Reactive Energy:", ct.LeadReactiveEnergyKVArh,"kVArh")
    #print("Lagging Reactive Energy:", ct.LagReactiveEnergyKVArh,"kVArh")
    print("")
    
# Checking the connection Modbus
try:
    # Setup Raspberry Pi as Modbus client/master
    client = ModbusClient(method=method, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client.connect()
    print("Connected to Modbus Communication")
    print("")

    # Enable register writting command
    ct1.enable_register_access(client=client)
    #ct1.send_command(client=client, command="enable_register_access", param=1)
    print("")
except BaseException as e:
    print(e)
    print("Cannot find Modbus Communication")
    print("")


# Checking the connection MySQL
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

    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `tesla_apaato_1`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, Active_Power_W, Reactive_Power_VAr, "
              "Consumed_Energy_Wh, Generated_Energy_Wh, Total_Reactive_Energy_VArh, "
              "Consumed_Energy_kWh, Generated_Energy_kWh, Total_Reactive_Energy_kVArh) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
except BaseException as e:
    print(e)
    print("Cannot access MySQl Server")
    print("")

# time counter
start = datetime.datetime.now()
first = [True, True]

# Reading a Modbus Message
while True:
    try:
        ## CT1 Monitoring Sequence
        if first[0] == True:
            first[0] = False

            # Reset accumulated values for first time measurements
            ct1.reset_all_values(client=client)
            #ct1.send_command(client=client, command="reset_all_values", param=1)
            print("")
            
        # Send the command to read the measured value
        ct1.send_command(client=client, command="read_measurement")
        cpu_temp = get_cpu_temperature()

        # Print the data
        timer = datetime.datetime.now()
        print("CT1 MEASUREMENTS")
        print_response(ct1)

        # Save the measured value
        Voltage.append(ct1.Voltage)
        Current.append(ct1.Current)
        PowerFactor.append(ct1.PowerFactor)
        ActivePowerW.append(ct1.ActivePowerW)
        ReactivePowerVAr.append(ct1.ReactivePowerVAr)
        
        # time counter
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            
            # Write data in database
            cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                round(sum(Voltage)/len(Voltage),2),
                                round(sum(Current)/len(Current),2),
                                round(sum(PowerFactor)/len(PowerFactor),2),
                                round(sum(ActivePowerW)/len(ActivePowerW),2),
                                round(sum(ReactivePowerVAr)/len(ReactivePowerVAr),2),
                                0,
                                0,
                                0,
                                ct1.ConsumedEnergyKWh,
                                ct1.GeneratedEnergyKWh,
                                ct1.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data CT1 is sent to database")
            print("")

            # alter custom values for next measurements
            Voltage = [Voltage[-1]]
            Current = [Current[-1]]
            PowerFactor = [PowerFactor[-1]]
            ActivePowerW = [ActivePowerW[-1]]
            ReactivePowerVAr = [ReactivePowerVAr[-1]]
        
        time.sleep(measure_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("====== ====== retrying ====== ======")
        time.sleep(5)
        pass

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
import os

#time.sleep(10)     # wait for RaspberryPi to complete its boot-up sequence
cpu_temp = None     # RaspberryPi temperature for hardware fault monitoring

# Define communication parameters
port = "/dev/ttyS0"
method = 'rtu'
bytesize = 8
stopbits = 2
parity = 'N'
baudrate = 9600   # data/byte transmission speed (in bytes per second)
server_latency = 50   # the delay time slave/server takes from completing command/request to sending the response (in milliseconds)
client_latency = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout = 5   # the maximum time the master/client will wait for response from slave/server (in seconds)
measure_delay = 5   # the period between each subsequent measurement (in seconds)
update_delay = 300   # the period between each subsequent update to database (in seconds)

# Define the Modbus's slave/server (nodes) and the master/client transmission waiting time
ct1 = omron.node(unit=1, delay=client_latency)
ct2 = omron.node(unit=2, delay=client_latency)

# Initiate measurement variable for custom value calculation
Voltage = [[],[]]
Current = [[],[]]
PowerFactor = [[],[]]
ActivePowerW = [[],[]]
ReactivePowerVAr = [[],[]]
ConsumedEnergyWh = [0, 0]
GeneratedEnergyWh = [0, 0]
TotalReactiveEnergyVArh = [0, 0]

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
    print("Consumed Energy        :", ct.ConsumedEnergyWh,"Wh")
    print("Generated Energy       :", ct.GeneratedEnergyWh,"Wh")
    #print("Leading Reactive Energy:", ct.LeadReactiveEnergyVArh,"VArh")
    #print("Lagging Reactive Energy:", ct.LagReactiveEnergyVArh,"VArh")
    print("Total Reactive Energy  :", ct.TotalReactiveEnergyVArh,"VArh")
    print("Consumed Energy        :", ct.ConsumedEnergyKWh,"kWh")
    print("Generated Energy       :", ct.GeneratedEnergyKWh,"kWh")
    #print("Leading Reactive Energy:", ct.LeadReactiveEnergyKVArh,"kVArh")
    #print("Lagging Reactive Energy:", ct.LagReactiveEnergyKVArh,"kVArh")
       # the period between each subsequent update to database (in seconds)
    print("")
    
# Checking the connection Modbus
try:
    # Setup Raspberry Pi as Modbus client/master
    client = ModbusClient(method=method, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client.connect()
    print("Connected to Modbus Communication")
    print("")

    # Set the slave/server transmission waiting time (latency)
    ct1.shift_to_setting(client=client)
    ct1.send_command(client=client, command="set_server_transmission_delay", param=server_latency)
    ct1.shift_to_measurement(client=client)
    print("")
    ct2.shift_to_setting(client=client)
    ct2.send_command(client=client, command="set_server_transmission_delay", param=server_latency)
    ct2.shift_to_measurement(client=client)
    print("")
    
except:
    print("Cannot find Modbus Communication")


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
    add_c2 = ("INSERT INTO `tesla_apaato_2`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, Active_Power_W, Reactive_Power_VAr, "
              "Consumed_Energy_Wh, Generated_Energy_Wh, Total_Reactive_Energy_VArh, "
              "Consumed_Energy_kWh, Generated_Energy_kWh, Total_Reactive_Energy_kVArh) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
except:
    print("Cannot access MySQl Server")

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
            ct1.shift_to_setting(client=client)
            ct1.send_command(client=client, command="change_ConsumedEnergyWh", param=0)
            ct1.send_command(client=client, command="change_GeneratedEnergyWh", param=0)
            ct1.send_command(client=client, command="change_TotalReactiveEnergyVArh", param=0)
            ct1.send_command(client=client, command="change_ConsumedEnergyKWh", param=0)
            ct1.send_command(client=client, command="change_GeneratedEnergyKWh", param=0)
            ct1.send_command(client=client, command="change_TotalReactiveEnergyKVArh", param=0)
            ct1.shift_to_measurement(client=client)
            print("")
            ct2.shift_to_setting(client=client)
            ct2.send_command(client=client, command="change_ConsumedEnergyWh", param=0)
            ct2.send_command(client=client, command="change_GeneratedEnergyWh", param=0)
            ct2.send_command(client=client, command="change_TotalReactiveEnergyVArh", param=0)
            ct2.send_command(client=client, command="change_ConsumedEnergyKWh", param=0)
            ct2.send_command(client=client, command="change_GeneratedEnergyKWh", param=0)
            ct2.send_command(client=client, command="change_TotalReactiveEnergyKVArh", param=0)
            ct2.shift_to_measurement(client=client)
            print("")
            
        # Send the command to read the measured value
        ct1.send_command(client=client, command="read_measurement")
        ct2.send_command(client=client, command="read_measurement")
        cpu_temp = get_cpu_temperature()

        # Print the data
        timer = datetime.datetime.now()
        print("CT1 MEASUREMENTS")
        print_response(ct1)
        print("CT2 MEASUREMENTS")
        print_response(ct2)

        # Save the measured value
        Voltage[0].append(ct1.Voltage)
        Voltage[1].append(ct2.Voltage)
        Current[0].append(ct1.Current)
        Current[1].append(ct2.Current)
        PowerFactor[0].append(ct1.PowerFactor)
        PowerFactor[1].append(ct2.PowerFactor)
        ActivePowerW[0].append(ct1.ActivePowerW)
        ActivePowerW[1].append(ct2.ActivePowerW)
        ReactivePowerVAr[0].append(ct1.ReactivePowerVAr)
        ReactivePowerVAr[1].append(ct2.ReactivePowerVAr)
        
        # time counter
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            
            # Write data in database
            cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                round(sum(Voltage[0])/len(Voltage[0]),2),
                                round(sum(Current[0])/len(Current[0]),2),
                                round(sum(PowerFactor[0])/len(PowerFactor[0]),2),
                                round(sum(ActivePowerW[0])/len(ActivePowerW[0]),2),
                                round(sum(ReactivePowerVAr[0])/len(ReactivePowerVAr[0]),2),
                                ct1.ConsumedEnergyWh-ConsumedEnergyWh[0],
                                ct1.GeneratedEnergyWh-GeneratedEnergyWh[0],
                                ct1.TotalReactiveEnergyVArh-TotalReactiveEnergyVArh[0],
                                ct1.ConsumedEnergyKWh,
                                ct1.GeneratedEnergyKWh,
                                ct1.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data CT1 is sent to database")
            print("")

            # Write data in database
            cur.execute(add_c2,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                round(sum(Voltage[1])/len(Voltage[1]),2),
                                round(sum(Current[1])/len(Current[1]),2),
                                round(sum(PowerFactor[1])/len(PowerFactor[1]),2),
                                round(sum(ActivePowerW[1])/len(ActivePowerW[1]),2),
                                round(sum(ReactivePowerVAr[1])/len(ReactivePowerVAr[1]),2),
                                ct2.ConsumedEnergyWh-ConsumedEnergyWh[1],
                                ct2.GeneratedEnergyWh-GeneratedEnergyWh[1],
                                ct2.TotalReactiveEnergyVArh-TotalReactiveEnergyVArh[1],
                                ct2.ConsumedEnergyKWh,
                                ct2.GeneratedEnergyKWh,
                                ct2.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data CT2 is sent to database")
            print("")

            # alter custom values for next measurements
            Voltage = [[Voltage[0][-1]], [Voltage[1][-1]]]
            Current = [[Current[0][-1]], [Current[1][-1]]]
            PowerFactor = [[PowerFactor[0][-1]], [PowerFactor[1][-1]]]
            ActivePowerW = [[ActivePowerW[0][-1]], [ActivePowerW[1][-1]]]
            ReactivePowerVAr = [[ReactivePowerVAr[0][-1]], [ReactivePowerVAr[1][-1]]]
            ConsumedEnergyWh = [ct1.ConsumedEnergyWh, ct2.ConsumedEnergyWh]
            GeneratedEnergyWh = [ct1.GeneratedEnergyWh, ct2.GeneratedEnergyWh]
            TotalReactiveEnergyVArh = [ct1.TotalReactiveEnergyVArh, ct2.TotalReactiveEnergyVArh]
        
        time.sleep(measure_delay)
    
    except BaseException as e:
        print("============")
        # Print the error message
        print("problem with -->",e)
        print("============")
        time.sleep(5)
        pass

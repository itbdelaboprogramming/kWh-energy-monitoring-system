"""
#!/usr/bin/env python
#title           :modbusPowerMeter.py
#description     :modbus Communication between Omron KM-N1-FLK and Raspberry Pi + RS485/CAN Hat
#author          :Fajar Muhammad Noor Rozaqi, Nicholas Putra Rihandoko
#date            :2023/04/07
#version         :1.1
#usage           :BMS-python
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

#time.sleep(10) # wait for RaspberryPi to complete its boot-up sequence

# Define communication parameters
port = "/dev/ttyS0"
method = 'rtu'
timeout = 5
bytesize = 8
stopbits = 2
baudrate = 9600
parity = 'N'
update_delay = 300 # 5 minutes

# Define the Modbus's slave/server (nodes)
ct1 = omron.node(unit=1, delay=0.05)
ct2 = omron.node(unit=2, delay=0.05)

# Initiate measurement variable for custom value calculation
Voltage = [[],[]]
Current = [[],[]]
PowerFactor = [[],[]]
ActivePowerW = [[],[]]
ReactivePowerVAr = [[],[]]
ConsumedEnergyWh = [0, 0]
GeneratedEnergyWh = [0, 0]
TotalReactiveEnergyVArh = [0, 0]

def print_response(ct):
    # Uncomment as needed
    print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
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
    print("Total Reactive Energy  :", ct.TotalReactiveEnergyKVArh,"kVArh")
    print("")
    
# Checking the connection Modbus
try:
    # Setup Raspberry Pi as Modbus client/master
    client = ModbusClient(method=method, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client.connect()
    print("Connected to Modbus Communication")
    print("")
except:
    print("Cannot find Modbus Communication")


# Checking the connection MySQL
try:
    # Setup Raspberry Pi as Database client
    db = pymysql.connect(host='syohin-e32-mysql.at.remote.it',      # Remote.it
                        port=33000,                                 # Remote.it
                        user='pi',                                  # MySQL
                        password='raspberrypi',                     # MySQL
                        db='test')                                  # MySQL
    cur = db.cursor()
    print("Connected to MySQl Server")
    print("")
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
            time.sleep(5)
            ct2.shift_to_setting(client=client)
            ct2.send_command(client=client, command="change_ConsumedEnergyWh", param=0)
            ct2.send_command(client=client, command="change_GeneratedEnergyWh", param=0)
            ct2.send_command(client=client, command="change_TotalReactiveEnergyVArh", param=0)
            ct2.send_command(client=client, command="change_ConsumedEnergyKWh", param=0)
            ct2.send_command(client=client, command="change_GeneratedEnergyKWh", param=0)
            ct2.send_command(client=client, command="change_TotalReactiveEnergyKVArh", param=0)
            ct2.shift_to_measurement(client=client)
            
        # Send the command to read the measured value
        ct1.send_command(client=client, command="read_measurement")
        ct2.send_command(client=client, command="read_measurement")

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
            add_c1 = "INSERT INTO `tesla_apaato_1`(DateTime, Voltage_V, Current_A, PF, Active_Power_W, Reactive_Power_VAr, Consumed_Energy_Wh, Generated_Energy_Wh, Total_Reactive_Energy_VArh, Consumed_Energy_kWh, Generated_Energy_kWh, Total_Reactive_Energy_kVArh) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                sum(Voltage[0])/len(Voltage[0]),
                                sum(Current[0])/len(Current[0]),
                                sum(PowerFactor[0])/len(PowerFactor[0]),
                                sum(ActivePowerW[0])/len(ActivePowerW[0]),
                                sum(ReactivePowerVAr[0])/len(ReactivePowerVAr[0]),
                                ct1.ConsumedEnergyWh-ConsumedEnergyWh[0],
                                ct1.GeneratedEnergyWh-GeneratedEnergyWh[0],
                                ct1.TotalReactiveEnergyVArh-TotalReactiveEnergyVArh[0],
                                ct1.ConsumedEnergyKWh,
                                ct1.GeneratedEnergyKWh,
                                ct1.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data CT1 is sent to database")

            # Write data in database
            add_c2 = "INSERT INTO `tesla_apaato_2`(DateTime, Voltage_V, Current_A, PF, Active_Power_W, Reactive_Power_VAr, Consumed_Energy_Wh, Generated_Energy_Wh, Total_Reactive_Energy_VArh, Consumed_Energy_kWh, Generated_Energy_kWh, Total_Reactive_Energy_kVArh) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(add_c2,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                sum(Voltage[1])/len(Voltage[1]),
                                sum(Current[1])/len(Current[1]),
                                sum(PowerFactor[1])/len(PowerFactor[1]),
                                sum(ActivePowerW[1])/len(ActivePowerW[1]),
                                sum(ReactivePowerVAr[1])/len(ReactivePowerVAr[1]),
                                ct2.ConsumedEnergyWh-ConsumedEnergyWh[1],
                                ct2.GeneratedEnergyWh-GeneratedEnergyWh[1],
                                ct2.TotalReactiveEnergyVArh-TotalReactiveEnergyVArh[1],
                                ct2.ConsumedEnergyKWh,
                                ct2.GeneratedEnergyKWh,
                                ct2.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data CT2 is sent to database")

            # alter custom values for next measurements
            Voltage = [[Voltage[0][-1],Voltage[1][-1]]]
            Current = [[Current[0][-1], Current[1][-1]]]
            PowerFactor = [[PowerFactor[0][-1], PowerFactor[1][-1]]]
            ActivePowerW = [[ActivePowerW[0][-1], ActivePowerW[1][-1]]]
            ReactivePowerVAr = [[ReactivePowerVAr[0][-1], ReactivePowerVAr[1][-1]]]
            ConsumedEnergyWh = [ct1.ConsumedEnergyWh, ct2.ConsumedEnergyWh]
            GeneratedEnergyWh = [ct1.GeneratedEnergyWh, ct2.GeneratedEnergyWh]
            TotalReactiveEnergyVArh = [ct1.TotalReactiveEnergyVArh, ct2.TotalReactiveEnergyVArh]
        
        time.sleep(5)
    
    except BaseException as e:
        print("============")
        # Print the error message
        print("problem with -->",e)
        print("============")
        #time.sleep(0)
        #client.close()
        pass

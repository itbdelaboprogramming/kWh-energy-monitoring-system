"""
#title           :modbusPowerMeter.py
#description     :modbus Communication between Omron KM-N1-FLK and Raspberry Pi + RS485/CAN Hat
#author          :Nicholas Putra Rihandoko
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
import msystem_M5XWTU113 as msystem
import electricPowerCalc as calc
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
client_latency = 200   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
timeout = 5   # the maximum time the master/client will wait for response from slave/server (in seconds)
measure_delay = 0   # the period between each subsequent measurement (in seconds)
update_delay = 300   # the period between each subsequent update to database (in seconds)

# Define the Modbus's slave/server (nodes) and the master/client transmission waiting time
ct1 = msystem.node(unit=1, delay=client_latency)
ct2 = omron.node(unit=2, delay=client_latency)
ct3 = omron.node(unit=3, delay=client_latency)
ct = calc.electric([ct1,ct2,ct3])

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
    db = pymysql.connect(host='192.168.200.93',
                        #port=*****,
                        user='pi',   # MySQL user
                        password='raspberrypi',   # MySQL password
                        db='test')   # MySQL database
    cur = db.cursor()
    print("Connected to MySQl Server")
    print("")

    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `tesla_apaato_1_m`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    add_c2 = ("INSERT INTO `tesla_apaato_2_o`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    add_c3 = ("INSERT INTO `tesla_apaato_1_o`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    add_c4 = ("INSERT INTO `tesla_apaato_1_mc`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    add_c5 = ("INSERT INTO `tesla_apaato_2_oc`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    add_c6 = ("INSERT INTO `tesla_apaato_1_oc`"
              "(DateTime, RPi_Temp, Voltage_V, Current_A, PF, ActivePower_W, ReactivePower_W, ConsumedEnergy_kWh, GeneratedEnergy_kWh, TotalReactiveEnergy_kVAr) "
              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    
except:
    print("Cannot access MySQl Server")

# time counter
start = datetime.datetime.now()
first = [True, True]
last_ConsumedEnergy = [0, 0, 0, 0, 0, 0]
last_GeneratedEnergy = [0, 0, 0, 0, 0, 0]
last_TotalReactiveEnergy = [0, 0, 0, 0, 0, 0]

# Reading a Modbus Message
while True:
    try:
        ## CT1 Monitoring Sequence
        if first[0] == True:
            first[0] = False

            # Reset accumulated values for first time measurements
            
        # Send the command to read the measured value
        ct1.send_command(client=client, command="read_measurement")
        ct2.send_command(client=client, command="read_measurement")
        ct3.send_command(client=client, command="read_measurement")
        cpu_temp = get_cpu_temperature()
        ct.calculate_all([ct1.Voltage,ct2.Voltage,ct3.Voltage], [ct1.Current,ct2.Current,ct3.Current], [ct1.PowerFactor,ct2.PowerFactor,ct3.PowerFactor])

        # Print the data
        timer = datetime.datetime.now()
        print("MSYSTEM CT1 MEASUREMENTS")
        print_response(ct1)
        print("OMRON CT2 MEASUREMENTS")
        print_response(ct2)
        print("OMRON CT3 MEASUREMENTS")
        print_response(ct3)
        
        # time counter
        if (timer - start).total_seconds() > update_delay or first[1] == True:
            start = timer
            first[1] = False
            ct.calculate_all([ct1.Voltage,ct2.Voltage,ct3.Voltage], [ct1.Current,ct2.Current,ct3.Current], [ct1.PowerFactor,ct2.PowerFactor,ct3.PowerFactor], mode="end")
            # Write data in database
            cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct1.Voltage,
                                ct1.Current,
                                ct1.PowerFactor,
                                ct1.ActivePowerW,
                                ct1.ReactivePowerVAr,
                                ct1.ConsumedEnergyKWh,
                                ct1.GeneratedEnergyKWh,
                                ct1.TotalReactiveEnergyKVArh))
            db.commit()
            print("Data MSYSTEM CT1 is sent to database")
            print("")

            # Write data in database
            cur.execute(add_c2,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct2.Voltage,
                                ct2.Current,
                                ct2.PowerFactor,
                                ct2.ActivePowerW,
                                ct2.ReactivePowerVAr,
                                ct2.ConsumedEnergyWh/1000-last_ConsumedEnergy[1],
                                ct2.GeneratedEnergyWh/1000-last_GeneratedEnergy[1],
                                ct2.TotalReactiveEnergyVArh/1000-last_TotalReactiveEnergy[1]))
            db.commit()
            print("Data OMRON CT2 is sent to database")
            print("")

            # Write data in database
            cur.execute(add_c3,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct3.Voltage,
                                ct3.Current,
                                ct3.PowerFactor,
                                ct3.ActivePowerW,
                                ct3.ReactivePowerVAr,
                                ct3.ConsumedEnergyWh/1000-last_ConsumedEnergy[2],
                                ct3.GeneratedEnergyWh/1000-last_GeneratedEnergy[2],
                                ct3.TotalReactiveEnergyVArh/1000-last_TotalReactiveEnergy[2]))
            db.commit()
            print("Data OMRON CT3 is sent to database")
            print("")

            # Write data in database
            cur.execute(add_c4,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct.voltage_avg[0],
                                ct.current_avg[0],
                                ct.pf_avg[0],
                                ct.activePower_avg[0],
                                ct.reactivePower_avg[0],
                                ct.consumedEnergy[0]-last_ConsumedEnergy[3],
                                ct.generatedEnergy[0]-last_GeneratedEnergy[3],
                                ct.reactiveEnergy[0]-last_TotalReactiveEnergy[3]))
            db.commit()
            cur.execute(add_c5,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct.voltage_avg[1],
                                ct.current_avg[1],
                                ct.pf_avg[1],
                                ct.activePower_avg[1],
                                ct.reactivePower_avg[1],
                                ct.consumedEnergy[1]-last_ConsumedEnergy[4],
                                ct.generatedEnergy[1]-last_GeneratedEnergy[4],
                                ct.reactiveEnergy[1]-last_TotalReactiveEnergy[4]))
            db.commit()
            cur.execute(add_c6,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                                cpu_temp,
                                ct.voltage_avg[2],
                                ct.current_avg[2],
                                ct.pf_avg[2],
                                ct.activePower_avg[2],
                                ct.reactivePower_avg[2],
                                ct.consumedEnergy[2]-last_ConsumedEnergy[5],
                                ct.generatedEnergy[2]-last_GeneratedEnergy[5],
                                ct.reactiveEnergy[2]-last_TotalReactiveEnergy[5]))
            db.commit()
            print("Data CALC is sent to database")
            print("")

            # alter custom values for next measurements
            last_ConsumedEnergy = [0, ct2.ConsumedEnergyWh/1000, ct3.ConsumedEnergyWh/1000, ct.consumedEnergy[0], ct.consumedEnergy[1], ct.consumedEnergy[2]]
            last_GeneratedEnergy = [0, ct2.GeneratedEnergyWh/1000, ct3.GeneratedEnergyWh/1000, ct.generatedEnergy[0], ct.generatedEnergy[1], ct.generatedEnergy[2]]
            last_TotalReactiveEnergy = [0, ct2.TotalReactiveEnergyVArh/1000, ct3.TotalReactiveEnergyVArh/1000, ct.reactiveEnergy[0], ct.reactiveEnergy[1], ct.reactiveEnergy[2]]
        
        time.sleep(measure_delay)
    
    except BaseException as e:
        # Print the error message
        print("problem with -->",e)
        print("====== ====== retrying ====== ======")
        time.sleep(5)
        pass

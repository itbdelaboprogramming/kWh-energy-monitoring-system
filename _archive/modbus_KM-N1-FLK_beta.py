"""
#!/usr/bin/env python
#title           :modbus_KM-N1-FLK.py
#description     :modbus Communication between Omron KM-N1-FLK and Raspberry Pi + RS485/CAN Hat
#author          :Fajar Muhammad Noor Rozaqi, Nicholas Putra Rihandoko
#date            :2023/04/03
#version         :0.1
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

time.sleep(10) # wait for RaspberryPi to complete its boot-up sequence

# Define communication parameters
port = "/dev/ttyS0"
method = 'rtu'
timeout = 5
bytesize = 8
stopbits = 2
baudrate = 38400
parity = 'N'
delay = 0.02

def send_command(address,count,unit):
    # Send the command and read response with function_code = 0x03
    response = client.read_holding_registers(address=address, count=count, unit=unit)
    return response

def print_response(response,data_type):
    if data_type == "u":
        print("Voltage                :", (response.registers[1])/10,"V")
        print("Current                :", (response.registers[7])/1000,"A")
        print("Power_Factor           :", (response.registers[13])/100)
        print("Frequency              :", (response.registers[15])/10,"Hz")
        print("Active_Power           :", (response.registers[17])/10,"W")
        print("Reactive_Power         :", (response.registers[19])/10,"Var")
    elif data_type == "l":
        print("Consumed Energy        :", (response.registers[1]),"kWh")
        print("Generated Energy       :", (response.registers[3]),"kWh")
        print("Leading Reactive Energy:", (response.registers[5]),"kVArh")
        print("Lagging Reactive Energy:", (response.registers[7]),"kVArh")
        print("Total Reactive Energy  :", (response.registers[9]),"kVArh")
    

# Checking the connection Modbus
try:
    # Setup Raspberry Pi as Modbus client/master
    client = ModbusClient(method=method, port=port, stopbits=stopbits, bytesize=bytesize, parity=parity, baudrate=baudrate, timeout=timeout)
    client.connect()
    print("Connected to Modbus Communication")
    print("")
except:
    print("Cannot find Modbus Communication")

# Reading a Modbus Message
while True:
    try:
        # time counter
        timer = datetime.datetime.now()
        
        # Send the command to read the measured voltage, current, PF, frequency, and power value of CT1
        ct1_u = client.read_holding_registers(address=0x0000, count=20, unit=1)
        #time.sleep(delay)
        # Send the command to read the measured accumulated energy value of CT1
        ct1_l = client.read_holding_registers(address=0x0220, count=10, unit=1)
        
        # Send the command to read the measured voltage, current, PF, frequency, and power value of CT2
        #ct2_u = client.read_holding_registers(address=0x0000, count=20, unit=2)
        # Send the command to read the measured accumulated energy value of CT2
        #ct2_l = client.read_holding_registers(address=0x0220, count=10, unit=2)
        
        # Send the command to read the measured voltage, current, PF, frequency, and power value of CT3
        #ct3_u = client.read_holding_registers(address=0x0000, count=20, unit=3)
        # Send the command to read the measured accumulated energy value of CT3
        #ct3_l = client.read_holding_registers(address=0x0220, count=10, unit=3)
        
        # Send the command to read the measured voltage, current, PF, frequency, and power value of CT4
        #ct4_u = client.read_holding_registers(address=0x0000, count=20, unit=4)
        # Send the command to read the measured accumulated energy value of CT4
        #ct4_l = client.read_holding_registers(address=0x0220, count=10, unit=4)
        
        
        # Print the data
        print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
        print_response(ct1_u,"u")
        print_response(ct1_l,"l")
        print("")

        # Delay
        time.sleep(1)

        # Database Connection
#        db = pymysql.connect(host='nicholas-dell-mysql.at.remote.it',   # Remote.it
#                             port=33001,                                # Remote.it
#                             user='pi',                                 # MySQL
#                             password='raspberrypi',                    # MySQL
#                             db='scib')                                 # MySQL

#        cur = db.cursor()

#        add_c0 = "INSERT INTO `monitoring_scib`(Timestamp, Temperature_Module_1,Temperature_Module_2, Voltage_Module_1, Voltage_Module_2, Current_Module_1, Current_Module_2, SoC) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
#        cur.execute(add_c0,((timer.strftime("%Y-%m-%d %H:%M"),
#                             t_battery_1,
#                             t_battery_2,
#                             v_battery_1_m,
#                             v_battery_2_m,
#                             i_battery_1_m,
#                             i_battery_2_m,
#                             soc_battery)))
#        db.commit()
#        print("Data is sent to database")
    
    except BaseException as e:
        print("============")
        # Prind the error message
        print("problem with -->",e)
        print("============")
        # time.sleep(0)
        #client.close()
        pass

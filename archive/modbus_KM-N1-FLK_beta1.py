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

#time.sleep(10) # wait for RaspberryPi to complete its boot-up sequence

class measObj:
    def __init__(self):
        self.Volt           = None
        self.Curr           = None
        self.PF             = None
        self.Freq           = None
        self.ActPow         = None
        self.RePow          = None
        self.ConsEn         = None
        self.GenEn          = None
        self.LeadReEn       = None
        self.LagReEn        = None
        self.TotalReEn      = None

    def save_read_u(self,response):
        self.Volt           = response.registers[1]/10      # Volts
        self.Curr           = response.registers[7]/1000    # Amps
        self.PF             = response.registers[13]/100
        self.Freq           = response.registers[15]/10     # Hz
        self.ActPow         = response.registers[17]/10     # Watt
        self.RePow          = response.registers[19]/10     # VAr

    def save_read_l(self,response):
        self.ConsEn         = response.registers[1]     # kWh
        self.GenEn          = response.registers[3]     # kWh
        self.LeadReEn       = response.registers[5]     # kWh
        self.LagReEn        = response.registers[7]     # kVArh
        self.TotalReEn      = response.registers[9]     # kVArh

def send_command(ct,unit,command):
    if command == "read_u":
        # Send the command and read response with function_code = 0x03 (3)
        response = client.read_holding_registers(address=0x0000, count=20, unit=unit)
        ct.save_read_u(response)
    elif command == "read_l":
        # Send the command and read response with function_code = 0x03 (3)
        response = client.read_holding_registers(address=0x0220, count=10, unit=unit)
        ct.save_read_l(response)
    #elif command == "write":
        # Send the command and read response with function_code = 0x10 (16)
        #response = client.write_registers(address=, count=, unit=unit)
    #elif command == "setting_mode":
        # Send the command and read response with function_code = 0x06 (6)
        #response = client.write_register(address=, count=, unit=unit)

def print_response(ct):
    print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
    print("Voltage                :", ct.Volt,"V")
    print("Current                :", ct.Curr,"A")
    print("Power_Factor           :", ct.PF)
    print("Frequency              :", ct.Freq,"Hz")
    print("Active_Power           :", ct.ActPow,"W")
    print("Reactive_Power         :", ct.RePow,"Var")
    print("Consumed Energy        :", ct.ConsEn,"kWh")
    print("Generated Energy       :", ct.GenEn,"kWh")
    print("Leading Reactive Energy:", ct.LeadReEn,"kVArh")
    print("Lagging Reactive Energy:", ct.LagReEn,"kVArh")
    print("Total Reactive Energy  :", ct.TotalReEn,"kVArh")
    print("")
    
# Define communication parameters
port = "/dev/ttyS0"
method = 'rtu'
timeout = 5
bytesize = 8
stopbits = 2
baudrate = 38400
parity = 'N'
transmission_delay = 0.1


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
    db = pymysql.connect(host='syohin-e32-mysql.at.remote.it',   # Remote.it
                        port=33000,                                 # Remote.it
                        user='pi',                                  # MySQL
                        password='raspberrypi',                     # MySQL
                        db='test')                                  # MySQL
    cur = db.cursor()
    print("Connected to MySQl Server")
    print("")
except:
    print("Cannot find Modbus Communication")


# Reading a Modbus Message
while True:
    try:
        # time counter
        timer = datetime.datetime.now()
        
        # Send the command to read the measured value of CT1
        ct1 = measObj()
        send_command(ct1,1,"read_u")
        time.sleep(transmission_delay)
        send_command(ct1,1,"read_l")
        time.sleep(transmission_delay)
        print_response(ct1)
        
        # Print the data
        print("CT1 MEASUREMENTS")
        print_response(ct1)
        
        add_c1 = "INSERT INTO `tesla_apaato_1`(DateTime, Voltage, Current, Active_Power, Reactive_Power, Consumed_Energy, Generated_Energy) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c1,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                            ct1.Volt,
                            ct1.Curr,
                            ct1.ActPow,
                            ct1.RePow,
                            ct1.ConsEn,
                            ct1.GenEn))
        db.commit()
        print("Data CT1 is sent to database")
        print("")
        print("")

        # Delay
        time.sleep(1)
        
        # time counter
        timer = datetime.datetime.now()

        # Send the command to read the measured value of CT2
        ct2 = measObj()
        send_command(ct2,2,"read_u")
        time.sleep(transmission_delay)
        send_command(ct2,2,"read_l")
        time.sleep(transmission_delay)
        
        # Print the data
        print("CT2 MEASUREMENTS")
        print_response(ct2)
        
        # Send to database
        add_c2 = "INSERT INTO `tesla_apaato_2`(DateTime, Voltage, Current, Active_Power, Reactive_Power, Consumed_Energy, Generated_Energy) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c2,(timer.strftime("%Y-%m-%d %H:%M:%S"),
                            ct2.Volt,
                            ct2.Curr,
                            ct2.ActPow,
                            ct2.RePow,
                            ct2.ConsEn,
                            ct2.GenEn))
        db.commit()
        print("Data CT2 is sent to database")
        print("")
        print("")

        # Delay
        time.sleep(1)
    
    except BaseException as e:
        print("============")
        # Print the error message
        print("problem with -->",e)
        print("============")
        #time.sleep(0)
        #client.close()
        pass

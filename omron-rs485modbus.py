"""
#!/usr/bin/env python
#title           :omron-rs485modbus.py
#description     :Communication between Raspberry Pi and Rs-485 Omron Power Meter.
#author          :Fajar Muhammad Noor Rozaqi
#date            :2020/09/01
#version         :0.1
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.8
#==============================================================================
"""
# Created by Fajar Muhammad Noor Rozaqi, NIW
# 1 september 2020, Takeo, Saga, Jpn

# Library
import serial # protcol serial communication in library python
import pymodbus # protocol modbus communication in library python
from pymodbus.pdu import ModbusRequest # protocol modbus request in library python
from pymodbus.client.sync import ModbusSerialClient as ModbusClient # protocol modbus serial client in library python
from pymodbus.transaction import ModbusRtuFramer # protocol modbus rtu in library python
import time # time clock in seconds 
import datetime # time clock in seconds
import pymysql # mysql connection in python

# checking connection ("UART")
client = ModbusClient(method='rtu', port='/dev/ttyUSB1', baudrate=38400, timeout = 2, stopbits = 2, btyesize = 8, parity = 'N') #'/dev/ttyUSB0
client.connect()
print("Connected to OMRON POWER METER KM-N1-FLK")

while True:
    try:
        # client.read_holding_registers(address = , count =, unit= )
        # address stands for 0x0000, it depends on the manual/registration address of device
        # count refers to how many sample the address
        # unit means the slave (each of device has unique slave)
        # print("Voltage 1 :{}, Voltage 2: {}, Voltage 3: {},Current 1 : {}, Current 2: {}, Current 3 : {},  Power Factor : {}, Frequency : {}, Active Power : {}, Passive Power : {}".format(ct1[01]/100))
        
        #counter
        timer = datetime.datetime.now()
        
        #Slave Number 1-4
        #CT_SCAN_ID1
        ct1     = client.read_holding_registers(address = 0x0000, count = 20,unit= 0x01)
        print("Time                   :", timer.strftime("%Y-%m-%d %H:%M"))
        print("Voltage_1              :", (ct1.registers[int(1)])/10,"V")
        print("Current_1              :", (ct1.registers[int(7)])/1000,"A")
        print("Power_Factor_1         :", (ct1.registers[int(13)])/100)
        print("Frequency_1            :", (ct1.registers[int(15)])/10,"Hz")
        print("Active_Power_1         :", (ct1.registers[int(17)])/10,"W")
        print("Reactive_Power_1       :", (ct1.registers[int(19)])/10,"Var")
        time.sleep(1)
        kwh1    = client.read_holding_registers(address = 0x0220, count = 2, unit = 0x01)
        print("Kwh_Id_1               :", kwh1.registers[int(1)],"kWh")
        print("room_id                :", int(1))
        print("")
        print("")
        time.sleep(5)
        
        #Database connection
        db = pymysql.connect(host='*********',
                             user= '*********',
                             password='*********',
                             db='*********')
        cur = db.cursor()

        add_c1 = "INSERT INTO `electrical_data_1`(vol_1, cur_1, power_factor, freq, power_active, power_passive, energy, room_id, date_entered) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c1,((ct1.registers[int(1)])/10,
                            (ct1.registers[int(7)])/1000,
                            (ct1.registers[int(13)])/100,
                            (ct1.registers[int(15)])/10,
                            (ct1.registers[int(17)])/10,
                            (ct1.registers[int(19)])/10,
                            kwh1.registers[int(1)],
                            int(1),
                            timer.strftime("%Y-%m-%d %H:%M")))
        db.commit()

        #CT_SCAN_ID2
        ct2     = client.read_holding_registers(address = 0x0000, count = 20,unit= 0x02)
        print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M"))
        print("Voltage_2              :", (ct2.registers[int(1)])/10,"V")
        print("Current_2              :", (ct2.registers[int(7)])/1000,"A")
        print("Power_Factor_2         :", (ct2.registers[int(13)])/100)
        print("Frequency_2            :", (ct2.registers[int(15)])/10,"Hz")
        print("Active_Power_2         :", (ct2.registers[int(17)])/10,"W")
        print("Reactive_Power_2       :", (ct2.registers[int(19)])/10,"Var")
        time.sleep(1)
        kwh2    = client.read_holding_registers(address = 0x0220, count = 2, unit = 0x02)
        print("Kwh_Id_2               :", kwh2.registers[int(1)],"kWh")
        print("room_id                :", int(2))
        print("")
        print("")
        time.sleep(5)
        
        #Database connection
        db = pymysql.connect(host='*********',
                             user= '*********',
                             password='*********',
                             db='*********')
        cur = db.cursor()

        add_c2 = "INSERT INTO `electrical_data_2`(vol_1, cur_1, power_factor, freq, power_active, power_passive, energy, room_id, date_entered) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c2,((ct2.registers[int(1)])/10,
                            (ct2.registers[int(7)])/1000,
                            (ct2.registers[int(13)])/100,
                            (ct2.registers[int(15)])/10,
                            (ct2.registers[int(17)])/10,
                            (ct2.registers[int(19)])/10,
                            kwh2.registers[int(1)],
                            int(2),
                            timer.strftime("%Y-%m-%d %H:%M")))
        db.commit()

        #CT_SCAN_ID3
        ct3     = client.read_holding_registers(address = 0x0000, count = 20,unit= 0x03)
        print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M"))
        print("Voltage_3              :", (ct3.registers[int(1)])/10,"V")
        print("Current_3              :", (ct3.registers[int(7)])/1000,"A")
        print("Power_Factor_3         :", (ct3.registers[int(13)])/100)
        print("Frequency_3            :", (ct3.registers[int(15)])/10,"Hz")
        print("Active_Power_3         :", (ct3.registers[int(17)])/10,"W")
        print("Reactive_Power_3       :", (ct3.registers[int(19)])/10,"Var")
        time.sleep(1)
        kwh3    = client.read_holding_registers(address = 0x0220, count = 2, unit = 0x03)
        print("Kwh_Id_3               :", kwh3.registers[int(1)],"kWh")
        print("room_id                :", int(3))
        print("")
        print("")
        time.sleep(5)
        
        #Database connection
        db = pymysql.connect(host='*********',
                             user= '*********',
                             password='*********',
                             db='*********')
        cur = db.cursor()

        add_c3 = "INSERT INTO `electrical_data_3`(vol_1, cur_1, power_factor, freq, power_active, power_passive, energy, room_id, date_entered) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c3,((ct3.registers[int(1)])/10,
                            (ct3.registers[int(7)])/1000,
                            (ct3.registers[int(13)])/100,
                            (ct3.registers[int(15)])/10,
                            (ct3.registers[int(17)])/10,
                            (ct3.registers[int(19)])/10,
                            kwh3.registers[int(1)],
                            int(3),
                            timer.strftime("%Y-%m-%d %H:%M")))
        db.commit()

        #CT_SCAN_ID4
        ct4     = client.read_holding_registers(address = 0x0000, count = 20,unit= 0x04)
        print("Time                   :", timer.strftime("%d/%m/%Y-%H:%M"))
        print("Voltage_4              :", (ct4.registers[int(1)])/10,"V")
        print("Current_4              :", (ct4.registers[int(7)])/1000,"A")
        print("Power_Factor_4         :", (ct4.registers[int(13)])/100)
        print("Frequency_4            :", (ct4.registers[int(15)])/10,"Hz")
        print("Active_Power_4         :", (ct4.registers[int(17)])/10,"W")
        print("Reactive_Power_4       :", (ct4.registers[int(19)])/10,"Var")
        time.sleep(1)
        kwh4    = client.read_holding_registers(address = 0x0220, count = 2, unit = 0x04)
        print("Kwh_Id_4               :", kwh4.registers[int(1)],"kWh")
        print("room_id                :", int(4))
        print("")
        print("")
        time.sleep(5)
        
        #Database connection
        db = pymysql.connect(host='*********',
                             user= '*********',
                             password='*********',
                             db='*********')
        cur = db.cursor()

        add_c4 = "INSERT INTO `electrical_data_4`(vol_1, cur_1, power_factor, freq, power_active, power_passive, energy, room_id, date_entered) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(add_c4,((ct4.registers[int(1)])/10,
                            (ct4.registers[int(7)])/1000,
                            (ct4.registers[int(13)])/100,
                            (ct4.registers[int(15)])/10,
                            (ct4.registers[int(17)])/10,
                            (ct4.registers[int(19)])/10,
                            kwh4.registers[int(1)],
                            int(4),
                            timer.strftime("%Y-%m-%d %H:%M")))
        db.commit()
        
        time.sleep(36)
    except:
        # print("============")
        # print("Disconnected")
        # print("============")
        # time.sleep(0)
        pass
    # time.sleep(1)
client.close()

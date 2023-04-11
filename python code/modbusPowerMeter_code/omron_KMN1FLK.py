"""
#!/usr/bin/env python
#title           :omron_KM-N1-FLK.py
#description     :modbus library for OMRON KM-N1-FLK
#author          :Nicholas Putra Rihandoko
#date            :2023/04/07
#version         :1.1
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
import time

class node:
    def __init__(self,unit,delay=0.02):
        self.Voltage                    = None
        self.Current                    = None
        self.PowerFactor                = None
        self.Frequency                  = None
        self.ActivePowerW               = None
        self.ReactivePowerVAr           = None
        self.ConsumedEnergyWh           = None
        self.GeneratedEnergyWh          = None
        self.LeadReactiveEnergyVArh     = None
        self.LagReactiveEnergyVArh      = None
        self.TotalReactiveEnergyVArh    = None
        self.ConsumedEnergyKWh          = None
        self.GeneratedEnergyKWh         = None
        self.LeadReactiveEnergyKVArh    = None
        self.LagReactiveEnergyKVArh     = None
        self.TotalReactiveEnergyKVArh   = None
        self.unit                       = unit
        self.transmission_delay         = delay

    def save_read_u(self,response):
        self.Voltage            = response.registers[1]/10      # Volts
        self.Current            = response.registers[7]/1000    # Amps
        self.PowerFactor        = response.registers[13]/100
        self.Frequency          = response.registers[15]/10     # Hz
        self.ActivePowerW       = response.registers[17]/10     # Watt
        self.ReactivePowerVAr   = response.registers[19]/10     # VAr

    def save_read_m(self,response):
        self.ConsumedEnergyWh           = response.registers[1]     # Wh
        self.GeneratedEnergyWh          = response.registers[3]     # Wh
        self.LeadReactiveEnergyVArh     = response.registers[5]     # Wh
        self.LagReactiveEnergyVArh      = response.registers[7]     # VArh
        self.TotalReactiveEnergyVArh    = response.registers[9]     # VArh

    def save_read_l(self,response):
        self.ConsumedEnergyKWh          = response.registers[1]     # kWh
        self.GeneratedEnergyKWh         = response.registers[3]     # kWh
        self.LeadReactiveEnergyKVArh    = response.registers[5]     # kWh
        self.LagReactiveEnergyKVArh     = response.registers[7]     # kVArh
        self.TotalReactiveEnergyKVArh   = response.registers[9]     # kVArh

    def shift_to_setting(self,client):
        # Send the command function_code = 0x06 (6)
        response = client.write_register(address=0xFFFF, value=0x0700, unit=self.unit)
        time.sleep(self.transmission_delay)
    
    def shift_to_measurement(self,client):
        # Send the command with function_code = 0x06 (6)
        response = client.write_register(address=0xFFFF, value=0x0400, unit=self.unit)
        time.sleep(self.transmission_delay)

    def writting_sequence(self,client,address,param,custom=None):
        # convert parameter input into two 4 bit hexadecimal format
        hex_param = hex(param)[2:].zfill(8)
        values = [val for val in [int(hex_param[i:i+4], 16) for i in (0, 4)]]

        # start writting sequence to send command with function_code = 0x10 (16)
        if custom==None:
            response = client.write_registers(address=address, values=values, unit=self.unit)
            time.sleep(self.transmission_delay)

        elif custom=="auto_shifting":
            self.shift_to_setting(client)
            response = client.write_registers(address=address, values=values, unit=self.unit)
            time.sleep(self.transmission_delay)
            self.shift_to_measurement(client)

        return response

    def send_command(self,client,command,param=None,custom=None):
        # Send the command and read response with function_code = 0x03 (3)
        if command == "read_measurement":
            response = client.read_holding_registers(address=0x0000, count=20, unit=self.unit)
            self.save_read_u(response)
            time.sleep(self.transmission_delay)
            response = client.read_holding_registers(address=0x0200, count=10, unit=self.unit)
            self.save_read_m(response)
            time.sleep(self.transmission_delay)
            response = client.read_holding_registers(address=0x0220, count=10, unit=self.unit)
            self.save_read_l(response)
            time.sleep(self.transmission_delay)
            #print("-- read is a success --")
            return
        # start writting sequence to send command with function_code = 0x10 (16)
        elif command == "phase_wire_config":
            address=0x2000
        elif command == "set_unit_number":
            address=0x2002
        elif command == "set_simple_measurement":
            address=0x200A
        elif command == "voltage_simple_measurement":
            address=0x200C
            param=param*10
        elif command == "PF_simple_measurement":
            address=0x200E
            param=param*100
        elif command == "voltage_assignment":
            address=0x2012
        elif command == "change_ConsumedEnergyWh":
            address=0x2600
        elif command == "change_GeneratedEnergyWh":
            address=0x2602
        elif command == "change_LeadReactiveEnergyVArh":
            address=0x2604
        elif command == "change_LagReactiveEnergyVArh":
            address=0x2606
        elif command == "change_TotalReactiveEnergyVArh":
            address=0x2608
        elif command == "change_ConsumedEnergyKWh":
            address=0x2620
        elif command == "change_GeneratedEnergyKWh":
            address=0x2622
        elif command == "change_LeadReactiveEnergyKVArh":
            address=0x2624
        elif command == "change_LagReactiveEnergyKVArh":
            address=0x2626
        elif command == "change_TotalReactiveEnergyKVArh":
            address=0x2628
        else:
            print("-- unrecognized command --")
            return
        
        # start writting sequence
        if param == None:
            print(" -- no parameter to be written, command was not completed --")
        else:
            self.writting_sequence(client=client, address=address, param=param, custom=custom)
            #print(" -- write is a success --")
            print(response)

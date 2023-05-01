"""
#title           :msystem_M5XWTU113.py
#description     :modbus library for MSYSTEM M5XWTU-113
#author          :Nicholas Putra Rihandoko
#date            :2023/04/07
#version         :0.2
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
import time

# the memory addresses are shifted down by two hex (lowest bit)

class node:
    def __init__(self,unit,delay=100):
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
        self.client_transmission_delay  = delay/1000    # in seconds

    def save_read_1(self,response):
        print(response.registers)
        print()
        self.Current            = response.registers[31]/1000    # Amps
        self.Voltage            = response.registers[1]/100     # Volt
        self.ActivePowerW       = response.registers[3]         # Watt
        self.ReactivePowerVAr   = response.registers[5]         # VAr
        self.PowerFactor        = response.registers[9]/10000
        self.Frequency          = response.registers[11]/100    # Hz

    def save_read_2(self,response):
        print(response.registers)
        print()
        self.ConsumedEnergyKWh          = response.registers[1]/10     # kWh
        self.LagReactiveEnergyKVArh     = response.registers[3]/10     # kVArh
        self.GeneratedEnergyKWh         = response.registers[7]/10     # kWh
        self.LeadReactiveEnergyKVArh    = response.registers[9]/10     # kVArh
        self.TotalReactiveEnergyKVArh   = response.registers[26]/10    # kVArh

    def enable_register_access(self,client):
        # Send the command with function_code = 0x06 (6)
        response = client.write_registers(address=4943, values=0x0001, unit=self.unit)
        time.sleep(3)
        return response
    
    def reset_all_values(self,client):
        # Send the command with function_code = 0x06 (6)
        response = client.write_registers(address=5328, values=0x0001, unit=self.unit)
        time.sleep(3)
        return response

    def writting_sequence(self,client,address,param):
        # convert parameter input into two 4 bit hexadecimal format
        hex_param = hex(param)[2:].zfill(4)
        #values = [val for val in [int(hex_param[i:i+4], 16) for i in (0, 4)]]
        values = [int(hex_param, 16)]

        # start writting sequence to send command with function_code = 0x10 (16)
        response = client.write_registers(address=address, values=values, unit=self.unit)
        time.sleep(self.client_transmission_delay)
        return response

    def send_command(self,client,command,param=None):
        # Send the command and read response with function_code = 0x03 (3)
        if command == "read_measurement":
            response = client.read_holding_registers(address=1, count=34, unit=self.unit)
            self.save_read_1(response)
            time.sleep(self.client_transmission_delay)
            response = client.read_holding_registers(address=127, count=28, unit=self.unit)
            self.save_read_2(response)
            time.sleep(self.client_transmission_delay)
            #print("-- read is a success --")
            return
        # start writting sequence to send command with function_code = 0x10 (16)
        elif command == "enable_register_access":
            address=4943
        elif command == "reset_all_values":
            address=5328
        else:
            print("-- unrecognized command --")
            return
        
        # start writting sequence
        if param == None:
            print(" -- no parameter to be written, command was not completed --")
        else:
            response = self.writting_sequence(client=client, address=address, param=param)
            #print(" -- write is a success --")
            print(response)

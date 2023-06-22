"""
#title           :yaskawa_D1000.py
#description     :modbus library for Converter YASKAWA D1000
#author          :Nicholas Putra Rihandoko
#date            :2023/05/08
#version         :0.1
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
import time

# FUNCTION CODE PYMODBUS SYNTAX
# 0x03 (3) = read_holding_registers
# 0x04 (4) = read_input_registers
# 0x06 (6) = write_register
# 0x10 (16) = write_registers

class node:
    def __init__(self,unit,name,client,delay=100):
        self._unit                      = unit
        self._name                      = name
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        # Write commands that is available, add if needed
        self.write_dict = {
            "write_something_register":     {"fc":0x06, "address":0xFFFF, "param":0x0700},
            "write_something_registers":    {"fc":0x10, "address":0x200C, "scale":10},
            "write_something_registers2":    {"fc":0x10, "address":0x200C}}

    def reset_read_attr(self):
        # Reset (and/or initiate) object's attributes
        self.DC_Voltage_command         = 0
        self.DC_Voltage_feedback        = 0
        self.DC_Current                 = 0
        self.AC_Voltage                 = 0
        self.AC_Current                 = 0
        self.DC_Power_kW                = 0
        self.AC_Power_kW                = 0
        self.AC_Frequency               = 0
        self.AC_Current_ref             = 0
        self.Power_Factor               = 0
        self.Active_Current             = 0
        self.Reactive_Current           = 0
        self.DC_Voltage_SFS_Out         = 0
        self.Consumed_Energy_GWh        = 0
        self.Consumed_Energy_MWh        = 0
        self.Consumed_Energy_kWh        = 0
        self.Generated_Energy_GWh       = 0
        self.Generated_Energy_MWh       = 0
        self.Generated_Energy_kWh       = 0

    def save_read(self,response,save,num):
        # Save responses to object's attributes
        if save == 1:
            self.DC_Voltage_command     = response.registers[0]         # Volts
            self.DC_Voltage_feedback    = response.registers[1]         # Volts
            self.DC_Current             = response.registers[2]/100     # Amps
            self.AC_Voltage             = response.registers[3]         # Volts
            self.AC_Current             = response.registers[4]/100     # Amps
            self.DC_Power_kW            = response.registers[5]/10      # kW
            self.AC_Power_kW            = response.registers[6]/10      # kW
            self.AC_Frequency           = response.registers[7]/10      # Hz
            self.AC_Current_ref         = response.registers[8]/100     # Amps
            self.Power_Factor           = response.registers[9]/100
            self.Active_Current         = response.registers[10]/10     # Amps
            self.Reactive_Current       = response.registers[11]/10     # Amps
            self.DC_Voltage_SFS_Out     = response.registers[12]        # Volts
        elif save == 2:
            self.Consumed_Energy_GWh        = response.registers[0]     # GWh
            self.Consumed_Energy_MWh        = response.registers[1]     # MWh
            self.Consumed_Energy_kWh        = response.registers[2]     # kWh
            self.Generated_Energy_GWh       = response.registers[3]     # GWh
            self.Generated_Energy_MWh       = response.registers[4]     # MWh
            self.Generated_Energy_kWh       = response.registers[5]     # kWh

    def reading_sequence(self,fc,address,count,save,num=0):        
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        if fc == 0x03:
            response = self._client.read_holding_registers(address=address, count=count, unit=self._unit)
        if fc == 0x04:
            response = self._client.read_input_registers(address=address, count=count, unit=self._unit)
        self.save_read(response,save,num)
        time.sleep(self._client_transmission_delay)
        return response

    def writting_sequence(self,fc,address,param):
        if param == None:
            print(" -- no parameter to be written, command was not completed --")
            return None
        # Send the command with function_code 0x06 (6) or 0x10 (16)
        if fc == 0x06:
            response = self._client.write_register(address=address, value=param, unit=self._unit)
        if fc == 0x10:
            # convert parameter input into two 4 bit hexadecimal format
            hex_param = hex(param)[2:].zfill(8)
            values = [val for val in [int(hex_param[i:i+4], 16) for i in (0, 4)]]
            response = self._client.write_registers(address=address, values=values, unit=self._unit)
        time.sleep(self._client_transmission_delay)
        return response

    def send_command(self,command,param=None):
        # Send the command and read response with function_code 0x03 (3)
        if command == "read_measurement":
            fc = 0x03
            response = self.reading_sequence(fc=fc, address=0x1080, count=14, save=1)
            response = self.reading_sequence(fc=fc, address=0x0820, count=6, save=2)
            #print("-- read is a success --")
            return
  
        # Send the command and read response with function_code 0x04 (4)
        if command == "read_others":
            fc = 0x04
            #response = self.reading_sequence(fc=fc, address=0x0000, count=16, save=1)
            #print("-- read is a success --")
            return
        
        # start writting sequence to send command with function_code 0x06 (6) or 0x10 (16)
        if self.write_dict.get(command) is not None:
            com = self.write_dict[command]
            if com.get("param") is not None:
                response = self.writting_sequence(fc=com["fc"], address=com["address"], param=com["param"])
            else:
                if com.get("scale") is not None:
                    response = self.writting_sequence(fc=com["fc"], address=com["address"], param=param*com["scale"])
                else:
                    response = self.writting_sequence(fc=com["fc"], address=com["address"], param=param)
            #print(response)
            #print(" -- write is a success --") 
            pass
        else:
            print("-- unrecognized command --")
            return
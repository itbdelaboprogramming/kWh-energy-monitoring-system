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

# FUNCTION CODE PYMODBUS SYNTAX
# 0x03 (3) = read_holding_registers
# 0x04 (4) = read_input_registers
# 0x06 (6) = write_register
# 0x10 (16) = write_registers

# the memory addresses are in 2 hex increment
# the memory addresses are shifted down by 2

class node:
    def __init__(self,unit,name,client,delay=300):
        self._name                      = name
        self._unit                      = unit
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        # Write commands that is available, add if needed
        self._write_dict = {
            "Enable_Register_Access":           {"fc":0x06, "address":4943, "param":0x0001},
            "Reset_All_Values":                 {"fc":0x06, "address":5328, "param":0x0001},
            "write_something_registers":        {"fc":0x10, "address":0x200C, "scale":10},
            "write_something_registers2":       {"fc":0x10, "address":0x200C}}
    
    def reset_read_attr(self):
        # Reset (and/or initiate) object's attributes
        for attr_name, attr_value in vars(self).items():
            if not attr_name.startswith("_"):
                setattr(self, attr_name, 0)

    def handle_sign(self,register):
        # Handle negative byte values
        signed_values = []
        for data in register:
            if data >= 0x8000:
                signed_value = -((data ^ 0xFFFF) + 1)  # Two's complement conversion
            else:
                signed_value = data
            signed_values.append(signed_value)
        return signed_values

    def save_read(self,response,save,num):
        reg = self.handle_sign(response.registers)
        # Save responses to object's attributes
        if save == 1:
            self.Current                = reg[31]/1000    # Amps
            self.Voltage                = reg[1]/100     # Volt
            self.Active_Power_W         = reg[3]         # Watt
            self.Reactive_Power_VAr     = reg[5]         # VAr
            self.Power_Factor           = reg[9]/10000
            self.Frequency              = reg[11]/100    # Hz
        elif save == 2:
            self.Consumed_Energy_kWh            = reg[1]/10     # kWh
            self.Lag_Reactive_Energy_kVArh      = reg[3]/10     # kVArh
            self.Generated_Energy_kWh           = reg[7]/10     # kWh
            self.Lead_Reactive_Energy_kVArh     = reg[9]/10     # kVArh
            self.Total_Reactive_Energy_kVArh    = reg[26]/10    # kVArh

    def reading_sequence(self,fc,address,count,save,num=None):        
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
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4) = read_input_registers
        if command == "read_measurement":
            fc = 0x03
            response = self.reading_sequence(fc=fc, address=1, count=34, save=1)
            response = self.reading_sequence(fc=fc, address=127, count=28, save=2)
            #print("-- read is a success --")
            return

        
        # Send the command and read response with function_code 0x04 (4)
        if command == "read_others":
            fc = 0x04
            #response = self.reading_sequence(fc=fc, address=0x0000, count=16, save=1)
            #print("-- read is a success --")
            return

        # start writting sequence to send command with function_code 0x06 (6) or 0x10 (16)
        if self._write_dict.get(command) is not None:
            com = self._write_dict[command]
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

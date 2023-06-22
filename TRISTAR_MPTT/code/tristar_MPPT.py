"""
#title           :tristar_MPPT.py
#description     :modbus library for Solar Charging System Controller TriStar MPPT
#author          :Nicholas Putra Rihandoko
#date            :2023/05/13
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
        self._write_dict = {
            "write_something_register":     {"fc":0x06, "address":0xFFFF, "param":0x0700},
            "write_something_registers":    {"fc":0x10, "address":0x200C, "scale":10},
            "write_something_registers2":    {"fc":0x10, "address":0x200C}}

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
            self._V_PU       = reg[0] + reg[1]/2**16        # Volts
            self._I_PU       = reg[2] + reg[3]/2**16        # Amps
        if save == 2:
            self.Battery_Voltage            = reg[0]*self._V_PU/2**15    # Volts
            self.Array_Voltage              = reg[3]*self._V_PU/2**15    # Volts
            self.Battery_Current            = reg[4]*self._I_PU/2**15    # Amps
            self.Array_Current              = reg[5]*self._I_PU/2**15    # Amps
            self.Heatsink_Temperature       = reg[11]                    # deg Celcius
            self.Battery_Reg_Temperature    = reg[13]                    # deg Celcius
        if save == 3:
            self.Ah_Charge_resetable        = reg[2]*0.1                             # Ah
            self.Output_Power_W             = reg[8]*self._V_PU*self._I_PU/2**17     # Watt
            self.Input_Power_W              = reg[9]*self._V_PU*self._I_PU/2**17     # Watt
        if save == 4:
            self.Total_Wh_Charge_daily      = reg[4]                                 # Wh

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
        address = None
        response = None
        # Send the command and read response with function_code 0x03 (3)
        if command == "read_measurement":
            fc = 0x03
            response = self.reading_sequence(fc=fc, address=0x0000, count=4, save=1)
            response = self.reading_sequence(fc=fc, address=0x0018, count=14, save=2)
            response = self.reading_sequence(fc=fc, address=0x0032, count=13, save=3)
            response = self.reading_sequence(fc=fc, address=0x0040, count=10, save=4)
            #print("-- read is a success --")
            return
  
        # Send the command and read response with function_code 0x04 (4)
        if command == "read_others":
            fc = 0x04
            #response = self.reading_sequence(fc=fc, address=0x0018, count=14, save=1)
            #response = self.reading_sequence(fc=fc, address=0x0026, count=12, save=2)
            #response = self.reading_sequence(fc=fc, address=0x0032, count=13, save=3)
            #response = self.reading_sequence(fc=fc, address=0x0040, count=10, save=4)
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
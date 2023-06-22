"""
#title           :omron_KMN1FLK.py
#description     :modbus library for OMRON KM-N1-FLK
#author          :Nicholas Putra Rihandoko
#date            :2023/04/13
#version         :1.5
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
        self._name                      = name
        self._unit                      = unit
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        # Write commands that is available, add if needed
        self._write_dict = {
            "Shift_to_Setting":                 {"fc":0x06, "address":0xFFFF, "param":0x0700},
            "Shift_to_Measurement":             {"fc":0x06, "address":0xFFFF, "param":0x0400},
            "set_Phase_Wire_Config":            {"fc":0x10, "address":0x2000},
            "set_Unit_Number":                  {"fc":0x10, "address":0x2002},
            "set_Simple_Measurement":           {"fc":0x10, "address":0x200A},
            "set_Voltage_Simple_Measurement":   {"fc":0x10, "address":0x200C, "scale":10},
            "set_PF_Simple_Measurement":        {"fc":0x10, "address":0x200E, "scale":100},
            "set_Voltage_Assignment":           {"fc":0x10, "address":0x2012},
            "set_Server_Transmission_Delay":    {"fc":0x10, "address":0x220A},
            "set_Consumed_Energy_Wh":           {"fc":0x10, "address":0x2600},
            "set_Generated_Energy_Wh":          {"fc":0x10, "address":0x2602},
            "set_Lead_Reactive_Energy_VArh":    {"fc":0x10, "address":0x2604},
            "set_Lag_Reactive_Energy_VArh":     {"fc":0x10, "address":0x2606},
            "set_Total_Reactive_Energy_VArh":   {"fc":0x10, "address":0x2608},
            "set_Consumed_Energy_kWh":          {"fc":0x10, "address":0x2620},
            "set_Generated_Energy_kWh":         {"fc":0x10, "address":0x2622},
            "set_Lead_Reactive_Energy_kVArh":   {"fc":0x10, "address":0x2624},
            "set_Lag_Reactive_Energy_kVArh":    {"fc":0x10, "address":0x2626},
            "set_Total_Reactive_Energy_kVArh":  {"fc":0x10, "address":0x2628}}       

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
            self.Voltage                = reg[1]/10      # Volts
            self.Current                = reg[7]/1000    # Amps
            self.Power_Factor           = reg[13]/100
            self.Frequency              = reg[15]/10     # Hz
            self.Active_Power_W         = reg[17]/10     # Watt
            self.Reactive_Power_VAr     = reg[19]/10     # VAr
        elif save == 2:
            self.Consumed_Energy_Wh             = reg[1]     # Wh
            self.Generated_Energy_Wh            = reg[3]     # Wh
            self.Lead_Reactive_Energy_VArh      = reg[5]     # VArh
            self.Lag_ReactiveEnergy_VArh        = reg[7]     # VArh
            self.Total_Reactive_Energy_VArh     = reg[9]     # VArh
        elif save == 3:
            self.Consumed_Energy_kWh            = reg[1]     # kWh
            self.Generated_Energy_kWh           = reg[3]     # kWh
            self.Lead_Reactive_Energy_kVArh     = reg[5]     # kVArh
            self.Lag_Reactive_Energy_kVArh      = reg[7]     # kVArh
            self.Total_Reactive_Energy_kVArh    = reg[9]     # kVArh

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
        # Send the command and read response with function_code 0x03 (3) 
        if command == "read_measurement":
            fc = 0x03
            response = self.reading_sequence(fc=fc, address=0x0000, count=20, save=1)
            response = self.reading_sequence(fc=fc, address=0x0200, count=10, save=2)
            response = self.reading_sequence(fc=fc, address=0x0220, count=10, save=3)
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
            
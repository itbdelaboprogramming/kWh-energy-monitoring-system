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

# the memory addresses are in 1 hex increment

class node:
    def __init__(self,unit,name,client,delay=200,max_count=20,increment=1,shift=0):
        self._name                      = name
        self._unit                      = unit
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        self._max_count                 = max_count     # maximum read/write address count in a single command
        self._shift                     = shift         # address shift
        self._inc                       = increment     # address increment
        # Commands and memory address that are available/configured, add if needed
        self._memory_dict = {
            ## read scaling values
            "V_PU_hi":             {"fc":0x03, "address":0x0000, "scale":1, "bias":0, "round":0},
            "V_PU_lo":             {"fc":0x03, "address":0x0001, "scale":1/(2**16), "bias":0, "round":5},
            "I_PU_hi":             {"fc":0x03, "address":0x0002, "scale":1, "bias":0, "round":0},
            "I_PU_lo":             {"fc":0x03, "address":0x0003, "scale":1/(2**16), "bias":0, "round":5},
            ## read
            "Battery_Voltage":      {"fc":0x03, "address":0x0018, "scale":1, "bias":0, "round":0},
            "Array_Voltage":        {"fc":0x03, "address":0x001B, "scale":1, "bias":0, "round":0},
            "Battery_Current":      {"fc":0x03, "address":0x001C, "scale":1, "bias":0, "round":0},
            "Array_Current":        {"fc":0x03, "address":0x001D, "scale":1, "bias":0, "round":0},
            "Heatsink_Temperature": {"fc":0x03, "address":0x0023, "scale":1, "bias":0, "round":0},
            "Battery_Temperature":  {"fc":0x03, "address":0x0025, "scale":1, "bias":0, "round":0},
            "Output_Power":         {"fc":0x03, "address":0x003A, "scale":1, "bias":0, "round":0}, # Watt
            "Input_Power":          {"fc":0x03, "address":0x003B, "scale":1, "bias":0, "round":0}, # Watt
            "Total_Wh_Charge_Daily":{"fc":0x03, "address":0x0044, "scale":1, "bias":0, "round":0}
            }
        # Used to shift the Modbus memory address for some devices
        for key in self._memory_dict: self._memory_dict[key]["address"] += shift
        # Extra calculation for parameters/data that is not readily available from Modbus, add if needed
        self._extra_calc = {
            "V_PU":                 {"scale":1, "bias":0, "round":5, "limit":[], "scale_dep":[[1,"V_PU_hi"]], "bias_dep":[[1,"V_PU_lo"]]},
            "I_PU":                 {"scale":1, "bias":0, "round":5, "limit":[], "scale_dep":[[1,"I_PU_hi"]], "bias_dep":[[1,"I_PU_lo"]]},
            "Battery_Voltage":      {"scale":1/(2**15), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Battery_Voltage"],[1,"V_PU"]], "bias_dep":[]},
            "Array_Voltage":        {"scale":1/(2**15), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Array_Voltage"],[1,"V_PU"]], "bias_dep":[]},
            "Battery_Current":      {"scale":1/(2**15), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Battery_Current"],[1,"I_PU"]], "bias_dep":[]},
            "Array_Current":        {"scale":1/(2**15), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Array_Current"],[1,"I_PU"]], "bias_dep":[]},
            "Output_Power":         {"scale":1/(2**17), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Output_Power"],[1,"V_PU"],[1,"I_PU"]], "bias_dep":[]},
            "Input_Power":          {"scale":1/(2**17), "bias":0, "round":2, "limit":[], "scale_dep":[[1,"Input_Power"],[1,"V_PU"],[1,"I_PU"]], "bias_dep":[]}
            }

    def reset_read_attr(self):
        # Reset (and/or initiate) object's attributes
        for attr_name, attr_value in vars(self).items():
            if not attr_name.startswith("_"): setattr(self, attr_name, 0)

    def map_read_attr(self,raw_address):
        # get the attribute data using its Modbus memory address
        mapped_addr = []
        for key, value in self._memory_dict.items():
            for a in sorted(raw_address):
                if value["address"] == a:
                    try: mapped_addr.append(getattr(self, key))
                    except:
                        mapped_addr.append(None)
                        print(" -- one or more mapped address has not been read from server --")
        return mapped_addr

    def handle_sign(self,register):
        # Handle negative byte values using 2's complement conversion
        signed_values = []
        for i, data in enumerate(register):
            if i % self._inc == 0:
                for b in range(self._inc-1,0,-1):
                    data = (data << 16) | register[i+b]
                if data >= (0x8000 << (16*(self._inc-1))):
                    signed_value = -int((data ^ ((1 << (16*self._inc)) - 1)) + 1)
                else: signed_value = int(data)
                signed_values.append(signed_value)
            else: signed_values.append(None)
        return signed_values

    def get_compile_dimension(self,array):
        # Get nested array dimension/size
        dim = []
        if isinstance(array, list):
            dim.append(len(array))
            inner_dim = self.get_compile_dimension(array[0])
            if inner_dim: dim.extend(inner_dim)
        return dim
    
    def create_copy_of_compile(self,size):
        # Build nested array with certain dimension/size
        if len(size) == 1: return [None] * size[0]
        else: return [self.create_copy_of_compile(size[1:]) for _ in range(size[0])]
        
    def copy_value_to_compile(self, array, copy_array):
        # Copy attribute_value to new array based on the compile blueprint (self._extra_calc[key]["compile"])
        if isinstance(array, list):
            for i, item in enumerate(array):
                if isinstance(item, list):
                    self.copy_value_to_compile(item, copy_array[i])
                elif isinstance(item, str):
                    if hasattr(self, item):
                        copy_array[i] = getattr(self, item)

    def handle_extra_calculation(self):
        # Additional computation for self._extra_calc parameters
        for key, value in self._extra_calc.items():
            if self._extra_calc[key].get("compile") is not None:
                # Make a same size array, copy the the dependency to the new array, assign it to new attribute
                dim = self.get_compile_dimension(value["compile"])
                comp = self.create_copy_of_compile(dim)
                self.copy_value_to_compile(value["compile"], comp)
                setattr(self, key, comp)
            else:
                val = 1
                # Calculate the parameters, assign it to new attribute, skip if dependency not met
                try:
                    for scale in value["scale_dep"]:
                        if getattr(self, scale[1]) != 0:
                            val *= getattr(self, scale[1])**scale[0]
                        else: val = 0
                    for bias in value["bias_dep"]:
                        val += getattr(self, bias[0])*getattr(self, bias[1])
                    val = round(val * value["scale"] + value["bias"], value["round"])
                    if value["limit"]:
                        if val < value["limit"][0]: val = value["limit"][1]
                    setattr(self, key, val)
                except AttributeError: pass

    def save_read(self,response,save):
        # Save responses to object's attributes
        s = 0
        for i, reg in enumerate(response):
            if s <= len(save)-1:
                if save[0].startswith('Hx'): start_save = int(save[0],16)
                else: start_save = self._memory_dict[save[0]]["address"]
                if save[s].startswith('Hx'):
                    if int(save[s],16) == start_save+i:
                        setattr(self, save[s], reg); s=s+1
                else:
                    if self._memory_dict[save[s]]["address"] == start_save+i:
                        val = round(reg * self._memory_dict[save[s]]["scale"] + self._memory_dict[save[s]]["bias"], self._memory_dict[save[s]]["round"])
                        setattr(self, save[s], val); s=s+1

    def count_address(self,fc,raw_address):
        # Configure the read address (final_addr) and the attribute name where the read value is saved (final_save)
        address, temp_addr, final_addr, save, temp_save, final_save = [], [], [], [], [], []

        # Match the address with the information in self._memory_dict library
        for key, value in self._memory_dict.items():
            if value["address"] in raw_address or key.lower() in raw_address:
                address.append(value["address"]); save.append(key)
                if fc == None: fc = value["fc"]
                raw_address = [x for x in raw_address if (x != value["address"] and x != key.lower())]
                if not raw_address: break

        # If the address is not available in the library, then use it as is
        for a in raw_address:
            if isinstance(a,str):
                print(" -- unrecognized address for '{}' --".format(a))
            else:
                address.append(a); save.append('Hx'+hex(a)[2:].zfill(4).upper())
                print(" -- address '{}' may gives raw data, use with discretion --".format(save[-1]))

        # Divide the address to be read into several command based on max_count
        address, save = zip(*sorted(zip(address, save)))
        address, save = list(address), list(save)
        for i, a in enumerate(address):
            if not temp_addr:
                temp_addr.append(a); temp_save.append(save[i])
            else:
                if a - temp_addr[0] + 1 <= self._max_count:
                    temp_addr.append(a); temp_save.append(save[i])
                else:
                    final_addr.append(temp_addr); final_save.append(temp_save)
                    temp_addr, temp_save = [a], [save[i]]
        if temp_addr: final_addr.append(temp_addr); final_save.append(temp_save)
        return fc, final_addr, final_save

    def reading_sequence(self,fc,address):
        response = None
        fc, addr, save = self.count_address(fc,address)            
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        if fc == 0x03:
            for i, a in enumerate(addr):
                response = self._client.read_holding_registers(address=a[0], count=a[-1]-a[0]+self._inc, unit=self._unit)
                self.save_read(self.handle_sign(response.registers),save[i])
                time.sleep(self._client_transmission_delay)
        elif fc == 0x04:
            for i, a in enumerate(addr):
                response = self._client.read_input_registers(address=a[0], count=a[-1]-a[0]+self._inc, unit=self._unit)
                self.save_read(self.handle_sign(response.registers),save[i])
                time.sleep(self._client_transmission_delay)
        else: print(" -- function code needs to be declared for this list of read address --")
        self.handle_extra_calculation()
        return response

    def handle_multiple_writting(self,param):
        # convert parameter input into hexadecimal format based on address increment
        if param < 0: hex_param = hex((abs(param) ^ ((1 << (16*self._inc)) - 1)) + 1)[2:].zfill(4*self._inc)
        else: hex_param = hex(param)[2:].zfill(4*self._inc)
        values = [int(hex_param[i:i+4], 16) for i in range(0, 4*self._inc, 4)]
        return values

    def writting_sequence(self,fc,address,param):
        response = None
        if isinstance(param, list):
            params = []
            for p in param: params.extend(self.handle_multiple_writting(p))
        else: params = self.handle_multiple_writting(param)
        # Send the command with function_code 0x06 (6) or 0x10 (16)
        if fc == 0x06:
            response = self._client.write_register(address=address, value=param, unit=self._unit)
        elif fc == 0x10:
            response = self._client.write_registers(address=address, values=params, unit=self._unit)
        time.sleep(self._client_transmission_delay)
        return response

    def handle_dependency(self,raw_address):
        # create list of read address based on the dependent parameters in self._extra_calc
        result = []
        for item in raw_address:
            if isinstance(item, list):
                result.extend(self.handle_dependency(item))
            else:
                if self._extra_calc.get(item):
                    for d in self._extra_calc.get(item)["scale_dep"]:
                        result.append(d[1].lower())
                    for d in self._extra_calc.get(item)["bias_dep"]:
                        result.append(d[1].lower())
                else: result.append(item.lower())
        return result

    def send_command(self,command,address,param=None,fc=None):
        response = None
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        if command == "read":
            address = [a.lower() if isinstance(a,str) else (a + self._shift) for a in address]
            for key, value in self._extra_calc.items():
                if key.lower() in address:
                    try: extra = self.handle_dependency(self._extra_calc[key]["compile"])
                    except KeyError: extra = self.handle_dependency([key])
                    address.extend(extra); address.remove(key.lower())
            response = self.reading_sequence(fc, address)

        # start writting sequence to send command with function_code 0x06 (6) or 0x10 (16)
        elif command == "write":
            if not isinstance(address,str): address += self._shift
            for key, value in self._memory_dict.items():
                if value["address"] == address or key.lower() == str(address).lower():
                    address = value["address"]
                    if fc == None:
                        fc = value["fc"]
                    if param == None:
                        if self._memory_dict[key].get("param") is not None:
                            param = value["param"]
                        else:
                            print(" -- no parameter to be written --"); return
                    else:
                        if self._memory_dict[key].get("scale") is not None:
                            param = param*value["scale"]
                    break
            
            if (fc == None) or (param == None) or isinstance(address,str):
                print(" -- incomplete input argument -- ")
            else:
                response = self.writting_sequence(fc, address, param)
                print("{} ({}) get: {}".format(key, str(hex(address)), response))

        else: print("-- unrecognized command --")
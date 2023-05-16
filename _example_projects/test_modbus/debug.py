
import logging

def debugging():
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

def print_response(server,cpu_temp,timer):
    # Uncomment as needed
    for i in range(len(server)):
        print(server[i]._name, "MEASUREMENTS")
        print("Time             :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
        print("CPU Temperature  :", cpu_temp, "degC")
        for attr_name, attr_value in vars(server[i]).items():
            if not isinstance(attr_value, list):
                if "SOC" in attr_name:
                    print(attr_name, "=", attr_value, "%")
                elif "Frequency" in attr_name:
                    print(attr_name, "=", attr_value, "Hz")
                elif "Voltage" in attr_name:
                    print(attr_name, "=", attr_value, "Volts")
                elif "Current" in attr_name:
                    print(attr_name, "=", attr_value, "Amps")
                elif "Power" in attr_name:
                    print(attr_name, "=", attr_value)
                elif "Energy" in attr_name:
                    print(attr_name, "=", attr_value)
                elif "Temperature" in attr_name:
                    print(attr_name, "=", attr_value, "degC")
            else:
                continue
                if not isinstance(attr_value[0], list):
                    print(attr_name, "=", attr_value)
                else:
                    for i in range(len(attr_value)):
                        print(attr_name, i+1, "=", attr_value[i])
        print("")
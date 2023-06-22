"""
#title           :debug.py
#description     :debugging functions for PyModbus, used through main.py file
#author          :Nicholas Putra Rihandoko
#date            :2023/05/12
#version         :0.1
#usage           :Modbus programming in Python
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

import logging
import subprocess
import datetime
import csv
import os

def debugging():
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

def print_response(server,cpu_temp,timer):
    #return
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
                elif ("Ah" in attr_name) or ("Wh" in attr_name) or ("Arh" in attr_name):
                    print(attr_name, "=", attr_value)
                elif "Temperature" in attr_name:
                    print(attr_name, "=", attr_value, "degC")
                elif "Count" in attr_name:
                    print(attr_name, "=", attr_value, )
            else:
                #continue
                if not isinstance(attr_value[0], list):
                    print(attr_name, "=", attr_value)
                else:
                    for i in range(len(attr_value)):
                        print(attr_name, i+1, "=", attr_value[i])
        print("")

def get_bootup_time():
    try:
        time = subprocess.check_output(['uptime', '-s']).decode().strip()
        return time
    except subprocess.CalledProcessError:
        return None
bootup_time = get_bootup_time()

def strval(array):
    string = " ".join(map(str, array))
    return string

def mtemp(array):
    var = [array[0][0], array[2][0], array[4][0], array[6][0],
            array[8][0], array[10][0], array[12][0], array[14][0]]
    return var

def update_database(server,db,cpu_temp,timer):
    #return
    # Define MySQL queries which will be used in the program
    add_c1 = ("INSERT INTO `kyuden_soc`"
                "(DateTime, RPi_Temp, Bat_Temp, SoC, Bat_Volt_Total, "
                "Bat_Volt_M1, Bat_Volt_M2, Bat_Volt_M3, Bat_Volt_M4, "
                "Bat_Volt_M5, Bat_Volt_M6, Bat_Volt_M7, Bat_Volt_M8, "
                "Bat_Volt_M9, Bat_Volt_M10, Bat_Volt_M11, Bat_Volt_M12, "
                "Bat_Volt_M13, Bat_Volt_M14, Bat_Volt_M15, Bat_Volt_M16, Conv_Chrg_Amps, Inv_Dchrg_Amps) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
    
    try:
        if server[2].DC_Bus_Voltage != 0:
            Inv_Dchrg_Amps = round(server[2].Output_Power_kW*1000/server[2].DC_Bus_Voltage,2)
        else:
            Inv_Dchrg_Amps = 0
        # Write data in database
        db.cursor().execute(add_c1,
                (timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp, strval(mtemp(server[0].Module_Temperature)), server[0].SOC, server[0].Total_Voltage,
                 strval(server[0].Cell_Voltage[0]), strval(server[0].Cell_Voltage[1]), strval(server[0].Cell_Voltage[2]), strval(server[0].Cell_Voltage[3]),
                 strval(server[0].Cell_Voltage[4]), strval(server[0].Cell_Voltage[5]), strval(server[0].Cell_Voltage[6]), strval(server[0].Cell_Voltage[7]),
                 strval(server[0].Cell_Voltage[8]), strval(server[0].Cell_Voltage[9]), strval(server[0].Cell_Voltage[10]), strval(server[0].Cell_Voltage[11]),
                 strval(server[0].Cell_Voltage[12]), strval(server[0].Cell_Voltage[13]), strval(server[0].Cell_Voltage[14]), strval(server[0].Cell_Voltage[15]),
                 server[1].DC_Current, Inv_Dchrg_Amps))
        db.commit()
        print("<===== Data is sent to database =====>")
        print("")
    except BaseException as e:
        # Print the error message
        print("Cannot update MySQl database")
        print("problem with -->",e)
        print("<===== ===== continuing ===== =====>")
        print("")

def log_in_csv(server,cpu_temp,timer,first_row=False):
    #return
    # Define the directory of the backup file and the data to be logged
    directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save/modbus_log.csv')
    column_title=["DateTime", "RPi_Temp", "Bat_Temp", "SoC", "Bat_Volt_Total",
                "Bat_Volt_M1", "Bat_Volt_M2", "Bat_Volt_M3", "Bat_Volt_M4",
                "Bat_Volt_M5", "Bat_Volt_M6", "Bat_Volt_M7", "Bat_Volt_M8",
                "Bat_Volt_M9", "Bat_Volt_M10", "Bat_Volt_M11", "Bat_Volt_M12",
                "Bat_Volt_M13", "Bat_Volt_M14", "Bat_Volt_M15", "Bat_Volt_M16", "Conv_Chrg_Amps", "Inv_Dchrg_Amps"]
    if server[2].DC_Bus_Voltage != 0:
        Inv_Dchrg_Amps = round(server[2].Output_Power_kW*1000/server[2].DC_Bus_Voltage,2)
    else:
        Inv_Dchrg_Amps = 0
    data=[timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp, strval(mtemp(server[0].Module_Temperature)), server[0].SOC, server[0].Total_Voltage,
                 strval(server[0].Cell_Voltage[0]), strval(server[0].Cell_Voltage[1]), strval(server[0].Cell_Voltage[2]), strval(server[0].Cell_Voltage[3]),
                 strval(server[0].Cell_Voltage[4]), strval(server[0].Cell_Voltage[5]), strval(server[0].Cell_Voltage[6]), strval(server[0].Cell_Voltage[7]),
                 strval(server[0].Cell_Voltage[8]), strval(server[0].Cell_Voltage[9]), strval(server[0].Cell_Voltage[10]), strval(server[0].Cell_Voltage[11]),
                 strval(server[0].Cell_Voltage[12]), strval(server[0].Cell_Voltage[13]), strval(server[0].Cell_Voltage[14]), strval(server[0].Cell_Voltage[15]),
                 server[1].DC_Current, Inv_Dchrg_Amps]
    # Write the data into csv file
    with open(directory, mode='a', newline='') as file:
        line = csv.writer(file, delimiter =',')
        if first_row:
            line.writerow(column_title)
        else:
            line.writerow(data)

def get_cpu_temperature():
    # Read CPU temperature from file
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp = round(float(f.read().strip())/1000,1)
    return temp

def calc_time_diff(start_datetime, end_datetime):
    # Convert time strings to datetime objects
    if isinstance(start_datetime, str):
        start = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
    elif isinstance(start_datetime, datetime):
        start = datetime.strftime(start_datetime, "%Y-%m-%d %H:%M:%S")
    if isinstance(end_datetime, str):
        end = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    elif isinstance(end_datetime, datetime):
        end = datetime.strftime(end_datetime, "%Y-%m-%d %H:%M:%S")
    # Calculate the time difference
    duration = end - start
    time_difference = duration.strftime("%d/%m/%Y-%H:%M:%S")
    return time_difference
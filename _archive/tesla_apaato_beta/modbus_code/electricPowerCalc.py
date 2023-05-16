
import datetime
import math

class electric:
    def __init__(self, unit):
        self.unit=unit
        self.voltage            = [[] for _ in range(len(self.unit))]   # Volts
        self.voltage_avg        = [None for _ in range(len(self.unit))] # Volts
        self.current            = [[] for _ in range(len(self.unit))]   # Amps
        self.current_avg        = [None for _ in range(len(self.unit))] # Amps
        self.pf                 = [[] for _ in range(len(self.unit))]
        self.pf_avg             = [None for _ in range(len(self.unit))]
        self.activePower        = [[] for _ in range(len(self.unit))]   # Watt
        self.activePower_avg    = [None for _ in range(len(self.unit))] # Watt
        self.activePower_last   = [0 for _ in range(len(self.unit))]    # Watt
        self.reactivePower      = [[] for _ in range(len(self.unit))]   # VAr
        self.reactivePower_avg  = [None for _ in range(len(self.unit))] # VAr
        self.reactivePower_last = [0 for _ in range(len(self.unit))]    # VAr
        self.consumedEnergy     = [0 for _ in range(len(self.unit))] # kWh
        self.generatedEnergy    = [0 for _ in range(len(self.unit))] # kWh
        self.reactiveEnergy     = [0 for _ in range(len(self.unit))] # kVAr

    def append_measurement(self, unit_voltage, unit_current, unit_pf):
        for i in range(len(self.unit)):
            self.voltage[i].append(unit_voltage[i])
            self.current[i].append(unit_current[i])
            self.pf[i].append(unit_pf[i])
            self.activePower[i].append(unit_voltage[i]*unit_current[i]*unit_pf[i])
            self.reactivePower[i].append(abs(unit_voltage[i]*unit_current[i]*math.sqrt(1-unit_pf[i]**2)))
        if len(self.pf[0]) > 1:
            self.activePower_last = [self.activePower[i][-2] for i in range(len(self.unit))]
            self.reactivePower_last = [self.reactivePower[i][-2] for i in range(len(self.unit))]

    def average_measurement(self):
        self.voltage_avg        = [round(sum(self.voltage[i])/len(self.voltage[i]),2) for i in range(len(self.unit))]
        self.current_avg        = [round(sum(self.current[i])/len(self.current[i]),2) for i in range(len(self.unit))]
        self.pf_avg             = [round(sum(self.pf[i])/len(self.pf[i]),3) for i in range(len(self.unit))]
        self.activePower_avg    = [round(sum(self.activePower[i])/len(self.activePower[i]),3) for i in range(len(self.unit))]
        self.reactivePower_avg  = [round(sum(self.reactivePower[i])/len(self.reactivePower[i]),3) for i in range(len(self.unit))]

    def calculate_energy(self):
        self.timer = datetime.datetime.now()
        dt=(self.timer - self.start).total_seconds()/(3600*1000)
        act=[((self.activePower[i][-1] + self.activePower_last[i])/2)*dt for i in range(len(self.unit))]
        react=[((self.reactivePower[i][-1] + self.reactivePower_last[i])/2)*dt for i in range(len(self.unit))]
        for i in range(len(self.unit)):
            if act[i] >= 0:
                self.consumedEnergy[i] = round(self.consumedEnergy[i] + act[i],6)
            else:
                self.generatedEnergy[i] = round(self.generatedEnergy[i] + abs(act[i]),6)
        self.reactiveEnergy = [round(self.reactiveEnergy[i] + react[i],6) for i in range(len(self.unit))]
        self.start = self.timer

    def reset_measurement(self):
        self.voltage        = [[i[-1]] for i in self.voltage]
        self.current        = [[i[-1]] for i in self.current]
        self.pf             = [[i[-1]] for i in self.pf]
        self.activePower    = [[i[-1]] for i in self.activePower]
        self.reactivePower  = [[i[-1]] for i in self.reactivePower]

    def calculate_all(self, volt=[0], current=[0], pf=[0], mode=None):
        if self.pf == [[] for _ in range(len(self.unit))]:
            self.start = datetime.datetime.now()
        for i in range(len(pf)):
            if pf[i] > 1:
                if i == 0:
                    pf[i] = 655.52 - pf[i]
                else:
                    pf[i] = 655.34 - pf[i]
                if pf[i] >= 1:
                    pf[i] = 0.99
                current[i] = -current[i]
        self.append_measurement(volt, current, pf)
        self.calculate_energy()
        if mode=="end":
            self.average_measurement()
            self.reset_measurement()
            
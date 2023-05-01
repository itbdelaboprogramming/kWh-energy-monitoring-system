import electricPowerCalc as calc
import time

ct1="a"
ct2="b"
ct3="c"

ct = calc.electric([ct1,ct2,ct3])

ct.calculate_all([101,102,103],[1.3,1.4,1.5],[0.93,0.93,0.93])
time.sleep(5)
ct.calculate_all([102,103,104],[1.2,1.3,1.4],[0.92,0.92,0.92])
time.sleep(5)
ct.calculate_all([103,104,105],[1.1,1.2,1.3],[0.91,0.91,0.91],mode="end")
print(ct.activeEnergy)
print(ct.voltage)
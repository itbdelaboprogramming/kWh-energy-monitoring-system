
param = int(0xffffff)

hex_param = hex(param)[2:].zfill(8)
print(hex_param)
values = [val for val in [int(hex_param[i:i+4], 16) for i in (0, 4)]]
#values = [int(hex_param, 16)]

print(values)
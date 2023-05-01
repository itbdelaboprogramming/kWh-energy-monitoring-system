v=[[1],[1]]
print(v)
v[0].append(0)
v[1].append(1)
v[0].append(1)
v[1].append(2)
v[0].append(None)
v[1].append(None)
v[0].append(3)
v[1].append(4)
print(v)
v = [[v[0][-1]],[v[1][-1]]]
print(v)
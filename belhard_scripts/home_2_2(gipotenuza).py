import math
a = int(input())
b = int(input())
gipot = math.sqrt(a**2+b**2)
s = 0.5*a*b
p = a + b + gipot
result = {'gipotenuza': gipot, 'acreage': s, 'Perimetr': p}
print(result)

a = {1: "two", 3: 'one', 7: 'one', 9: 'three', 5: 'three'}
b = list(a.items())
print(b)
#print(len(b))
d = {}
i = 0
y = i+1
while i <= (len(b)-1):
    if y <= (len(b)-1):
        if b[i][1] == b[y][1]:
            d[b[i][1]] = (b[i][0],b[y][0])
            #print(b[i],b[y])
            y = y + 1
            if y > (len(b)-1):
                #print("All Y elements has been looked")
                i = i + 1
                y = i + 1
        else:
            y = y + 1
            if y > (len(b)-1):
                #print("All Y elements has been looked2")
                i = i + 1
                y = i + 1
    else:
        print('The end')
        print(d)
        break
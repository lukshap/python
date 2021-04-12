simple = {0:'zero',1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine'}
complex = {11:'eleven',12:'twelve',13:'thirteen',14:'fourteen',15:'fivteen',16:'sixteen',17:'seventeen',18:'eighteen',19:'nineteen'}
desiat = {10:'ten',20:'twenty',30:'thirty',40:'fourty',50:'fifty',60:'sixty',70:'seventy',80:'eighty',90:'ninety'}
for i in list(range(99)):
    if len(str(i)) < 2:
        print(simple[i])
    elif len(str(i)) >= 2:
        if i in complex:
            print(complex[i])
        elif i in desiat:
            print(desiat[i])
        else:
            a = list(str(i))
            if int(a[0])*10 in desiat:
                y = int(a[0])*10
            if int(a[1]) in simple:
                yy = int(a[1])
            print(desiat[y]+' '+simple[yy])
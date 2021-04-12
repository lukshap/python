s=''
for i in open('names.txt'):
    s=i
    print(s)
s=s.replace('"','').split(",")
print(type(s))
print(s)
print(len(s))
s=sorted(s)
print(s)
def run(x):
    lst=[]
    for i in x.lower():
        lst.append(ord(i)-96)
    #print(lst)
    return sum(lst)
#str=''
i=1
y=0
for each in range(0,len(s)):
    y+=run(s[each])*i
    i+=1
print(y)
#print(str)
#print(run(str))
#str+=s[each]

import re     #importing module for regexps
f=open('Regexp1(for email).txt')
regexp='(' + f.read().rstrip()+ ')'
pattern=re.compile(regexp)   # regexp must put in (),for instance: re.compile("([A-Z][a-zA-Z_\-\.]{5,63}@[a-z]{3,8}\.(com|org|net))")
string='ffwfwwPluksha@gmail.net Faafafsa@gmail.comdgelrgl fwfw[ FAAAfwfew@mail.net'
rez=pattern.findall(string)
for i in range(len(rez)):
    print(rez[i][0])

f=open('Regexp2(for IP).txt')
regexp_full=f.read().rstrip()    #'25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]'
# regexp_full='{0}{0}{0}{0}'.format(regexp_octet)
print(regexp_full)
string='(192.168.1.99 sc 155.155.1.99 efw155.155.1.200)'
pattern=re.compile(regexp_full)                                  # regexp must put in ()
rez=pattern.findall(string)
print(rez)
lst=[]
count=0
k=0
j=0
while count < len(rez)/4:
    lst.append([])
    count+=1
for i in range(len(rez)):
        if j<=3:
            lst[k].append(rez[i])
            j+=1
        else:
            k+=1
            j=1
            lst[k].append(rez[i])
            continue
for i in(lst):
    print(i)

regexp='((\+|810)([0-9]{1,3})[ \-\(]?[0-9]{2}[ \-\)]?([0-9][ \-]?){7})'
string='+375296725927 810375(17 672-5-9 2 7'
pattern=re.compile(regexp) # regexp must put in ()
rez=pattern.findall(string)
for i in range(len(rez)):
    print(rez[i][0])

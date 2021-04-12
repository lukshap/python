class IP:
    def __init__(self,IP):
        self.__usualip=IP
        self.__desiatip=None
        self.__desiatmask=None
        self.__binarymask=None
        self.__lst=[]
    def __str__(self):
       return "usualip:{3}\ndesiatip:{0}\ndesiatmask:{1}\nbinarymask:{2}".format(self.__desiatip,self.__desiatmask,self.__binarymask,self.__usualip)
    def desiatip(self):
        self.__lst=self.__usualip.replace("/",".").split(".")
        j=1
        self.__desiatip=0
        for i in range(len(self.__lst)-1):
            self.__desiatip+=int(self.__lst[i])*256**((len(self.__lst)-1)-j)
            j+=1
    def binaryip(self):
        pass
    def desiatmask(self):
        lst=[[],[],[],[]]
        lst2=[[0],[0],[0],[0]]
        mask=int(self.__lst[-1])
        for i in range(mask//8):
            for j in range(8):
                lst[i].append(1)
                j+=1
        for j in range(mask%8):
            lst[i+1].append(1)
            j+=1
        while len(lst[i+1])<8:
            lst[i+1].append(0)
        for i in range(len(lst)):
            a=0
            y=0
            for j in range(1,len(lst[i])+1):
                a+=int(lst[i][-j])*2**y
                lst2[i]= a
                y+=1
        self.__desiatmask=str(lst2).replace("[","").replace("]","").replace(",",".").replace(" ","")
    def binarymask(self):
        lst=[[],[],[],[]]
        mask=int(self.__lst[-1])
        for i in range(mask//8):
            for j in range(8):
                lst[i].append(1)
                j+=1
        for j in range(mask%8):
            lst[i+1].append(1)
            j+=1
        while len(lst[i+1])<8:
            lst[i+1].append(0)
        self.__binarymask=str(lst).replace("[","").replace(",","").replace("]",".").replace(" ","")[0:-2]

a=IP('192.168.64.95/30')
b=IP('77.88.21.8/24')
a.desiatip()
a.desiatmask()
a.binarymask()
print(a)
#b.desiatip()
#b.desiatmask()
#b.binarymask()
#print(b)
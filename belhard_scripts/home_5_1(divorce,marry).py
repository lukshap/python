class human:
    # __all_instances=[]
    def __init__(self,i):
        self.__string=i
        self.__id=''
        self.__name=''
        self.__age =''
        self.__is_marriage=''
        self.__spouse=''
        self.set_info()
        # self.__class__.__all_instances.append(self)
    def __str__(self):
        return "id:{0},name:{1},age:{2},is_marriage:{3},spouse:{4}".format(self.__id,self.__name,self.__age,self.__is_marriage,self.__spouse)
    def set_info(self):
        lst = self.__string.rstrip().split('|')
        self.__id=int(lst[0])
        self.__name=lst[1]
        self.__age=int(lst[2])
        if lst[3]=='0':self.__is_marriage=False
        else:self.__is_marriage=True
        if lst[4]=='':self.__spouse=None
        else:self.__spouse=int(lst[4])
    def divorce(self):
        if self.__is_marriage==True:
            self.__is_marriage=False
            self.__spouse=None
    def get_id(self):
        return self.__id
    def get_spouse(self):
        return self.__spouse
    def marry(self,spouse_id):
        self.__is_marriage=True
        self.__spouse=spouse_id
    # @staticmethod #decorator
    # def get_all_instances():
    #     return human.__all_instances
lst = []
for i in open("file.csv"):
    if len(i)>0 and i[0].isdigit():
        a=human(i)
        lst.append(a)
for i in lst:
    print(i)
# for i in human.get_all_instances():
#     print(i)
a=input()
b=input()
for i in range(len(lst)):
    if lst[i].get_id()==int(a):
        mema=i
        lst[mema].divorce()
        for j in range(len(lst)):
            if lst[j].get_spouse()==lst[i].get_id():lst[j].divorce()
    if lst[i].get_id()==int(b):
        memb=i
        lst[memb].divorce()
        for j in range(len(lst)):
            if lst[j].get_spouse()==lst[i].get_id():lst[j].divorce()
lst[mema].marry(lst[memb].get_id())
lst[memb].marry(lst[mema].get_id())
for i in lst:
    print(i)
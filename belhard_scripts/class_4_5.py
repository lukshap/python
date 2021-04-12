class human:
    def __init__(self,name,age):
        self.__name=None
        self.__age=None
        self.set_age(age)
        #self.set_name(name)
    def __str__(self):
        return "age: {1} ; name:{0}".format(self.__name,self.__age)
    def get_age(self):
        return self.__age
    def set_age(self,age):
        self.__age=age
    age=property(get_age,set_age)


a=human("gdhfd",34)
#print(a.get_age())
a.set_age(13)
print(a)
a.age=4
print(a)

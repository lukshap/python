class human:
    def __init__(self,name,age):
        self.__name=name
        self.__age=age
        #self.set_age(age)
        #self.set_name(name)
    def __str__(self):
        return "age: {1} ; name:{0}".format(self.__name,self.__age)
    def get_age(self):
        return self.__age
    def set_age(self,age):
        self.__age=age


a=human("gdhfd",34)
print(a.get_age())
#a.set_age(13)
#print(a)

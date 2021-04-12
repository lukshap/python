class human:
    __counter_humans = 0
    def __init__(self,age,name):
        self.__age = age
        self.__name = name
        self.__class__.__counter_humans+=1
    def __str__(self):
        return "name: {} age:{}".format(self.__name,self.__age)
    @staticmethod
    def get_counter():
        return human.__counter_humans
    @staticmethod
    def set_counter():
        human.__counter_humans+=1
    def __eq__(self, other):
        return type(self)==type(other) and self.__age == other.__age and self.__name.lower() == other.__name.lower()

class woman(human):
    __counter_women = 0
    def __init__(self,age,name,some_attr):
        super().__init__(age,name)
        self.__some_attr = some_attr
        self.__class__.__counter_women+=1
        human.set_counter()
    @staticmethod
    def get_counter1():
         return woman.__counter_women
    def __str__(self):
        #return "{} some_attr = {}".format(super().__str__(),self.__some_attr)
        return "some_attr = {}".format(self.__some_attr)
    def __eq__(self, other):
        return super().__eq__(other) and self.__some_attr == other.__some_attr
a = woman(20,'Ann',1)
c = woman(20,'Ann',1)
print(a)
print(human.get_counter())
print(woman.get_counter1())
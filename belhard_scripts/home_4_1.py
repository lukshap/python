class human:
    __count=0 #static
    def __init__(self):
        self.__name=None
        self.__age=None
        #self.set_age(age)
        #self.set_name(name)
        self.__class__.__count+=1 # self.__class__ => output class (and it's name) of instance self
    def __str__(self):
       return "age: {1}\nname:{0}".format(self.__name,self.__age)
    @staticmethod #decorator
    def get_count():
        return human.__count
    def set_age(self,age):
        if type(age) == int:
            if age<=0:
               print('You should type right value')
            else:
                self.__age=age
        else:
            print('You should type int value')
    def get_age(self):
        return self.__age
    def set_name(self,name):
        if type(name) == str:
            if name.isalpha():
                self.__name=name.capitalize()
            else:
                print('You should type only letters')
        else:
            print('You should type str')
    def get_name(self):
        return self.__name

a=human()
print(type(a))
print(dir(a))
b=human()
a.set_age(88)
#print(a.get_age())
a.set_name('pasha')
#print(a.get_name())
print(a)
print(human.get_count())

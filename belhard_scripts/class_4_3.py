class human:
    def __init__(self,name,age):
        self.__name=name
        self.__age=age
    def __str__(self):
        return "name:" + self.__name + "\nage:" + str(self.__age)




a=human("Igor",18)
print(a)
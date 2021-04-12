class human():
    __count=0
    def __init__(self,name,age):
        self.__name=name
        self.__age=age
    def __str__(self):
        return "name:{0},age:{1}".format(self.__name,self.__age)
    @staticmethod
    def get_count():
        return human.__count
    @staticmethod
    def set_count():
        human.__count+=1
class humanoid(human):
    def __new__(self, name,age):
        human.set_count()
        if human.get_count()<=3:
            super().__new__(self)

a=humanoid('pasha',3)
print(a,type(a),"Number of instances class humanoid =",human.get_count())
a=humanoid('pasha',3)
print(a,type(a),"Number of instances class humanoid =",human.get_count())
a=humanoid('pasha',3)
print(a,type(a),"Number of instances class humanoid =",human.get_count())
a=human('pasha',10)
print(a,type(a),"Number of instances class humanoid =",human.get_count())
a=humanoid('pasha',3)
print(a,type(a),"Number of instances class humanoid =",human.get_count())
#
# try:
#     print(1)
#     # a = []
#     # a[1]=8
#     print(10/0)
#     print(2)
# except ZeroDivisionError as e:
#     print(e)
# except IndexError as e:
#     print(e)
# else:
#     print(4)
def division(a,b):
    if(b==0): raise ZeroDivisionError()
    return a/b

class MyOwnError(Exception):
    def __init__(self,str):
        super().__init__()
        self.error = str
    def __str__(self):
        return self.error



raise MyOwnError("sdjklgb")


with open('text.txt') as file:
    file.write("jlkghhngsdjg\n")
    for i in file:
        print(i)
from random import shuffle
class card:
    def __init__(self):
        self.__name=''
        self.__value=''
    def __str__(self):
        return "name:{0},value:{1}".format(self.__name,self.__value)
    def set_name(self,name,mast):
        self.__name=name+mast
    def set_value(self,value):
        self.__value=value
    def get_value(self):
        return self.__value
    def change_values_for_T(self):
        if self.__name[0]=='T' and self.__value==11:
           self.__value-=10
           return 1
class deck():
    __cards=['6','7','8','9','10','V','D','K','T']
    __mast=["\u2660","\u2663","\u2665","\u2666"]
    __values=[6,7,8,9,10,2,3,4,11]
    def __init__(self):     ##пробегаем по трем массивам и на каждой итерации создаем экземпляр класс Card и аппендим его в self.__cardsarray=[]
        self.__cardsarraydeck=[]
        for i in range(len(deck.__cards)):
            for j in deck.__mast:
                a=card()
                a.set_name(deck.__cards[i],j)
                a.set_value(deck.__values[i])
                self.__cardsarraydeck.append(a)
    def show_current_deck(self):
        for i in self.__cardsarraydeck:
            print(i)
        print('The total count cards in the deck is:',len(self.__cardsarraydeck))
    def get_card(self):
        self.__outside=self.__cardsarraydeck.pop() #Убираем карту из колоды
        print('The card "',self.__outside,'" went from the deck')
        return self.__outside
    def shuffler(self):            #тусуем колоду
        shuffle(self.__cardsarraydeck)
class hand():
    def __init__(self):
        self.__cardsarrayhand=[]
        self.__currentsum=0
    def add_card(self):
        self.__cardsarrayhand.append(deck1.get_card()) # берем карту в руку
    def set_totalsum(self):
        for i in self.__cardsarrayhand:
            self.__currentsum+=i.get_value()
        if self.__currentsum > 21:
            print('Aliarm!')
            for i in self.__cardsarrayhand:
                if i.change_values_for_T():
                    self.__currentsum-=10
                    break           #if in the deck more than 1 Tuz
    def show_current_hand(self,player_name):
        for i in self.__cardsarrayhand:
            print('The card "',i,'" is in the',player_name,'hand')
        print('The totalsum in the',player_name,'hand is',self.__currentsum)
        self.__currentsum=0
    def __contains__(self,key):
        pass

deck1=deck()
deck1.shuffler()
player1=hand()
player2=hand()

player1.add_card()
player1.set_totalsum()
player1.show_current_hand('player_1')
player1.add_card()
player1.set_totalsum()
player1.show_current_hand('player_1')

player2.add_card()
player2.set_totalsum()
player2.show_current_hand('player_2')
player2.add_card()
player2.set_totalsum()
player2.show_current_hand('player_2')

deck1.show_current_deck()


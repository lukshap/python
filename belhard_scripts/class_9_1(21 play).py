from random import shuffle
class card:
    def __init__(self,name,value):
        self.__name=name
        self.__value=value
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
                a=card(deck.__cards[i]+j,deck.__values[i])
                self.__cardsarraydeck.append(a)
    def show_current_deck(self):
        for i in self.__cardsarraydeck:
            print(i)
        print('The total count cards in the deck is:',len(self.__cardsarraydeck))
    def get_card(self):
        self.__outside=self.__cardsarraydeck.pop() #Убираем карту из колоды
        print('The card "',self.__outside,'" went from the deck','\n')
        return self.__outside
    def shuffler(self):            #тусуем колоду
        shuffle(self.__cardsarraydeck)
class hand():
    def __init__(self):
        self._cardsarrayhand=[]
        self._currentsum=0
        self._stoptakecard=False
        self._stoptakecardbot=False
    def add_card(self,player_name,card):
        if self._stoptakecard:print('The Game is over for',player_name,'\n\n')
        else:
            self._cardsarrayhand.append(card) # берем карту в руку!!!проверить
            self.show_current_hand(player_name)
    def set_currentsum(self,player_name):
        self._currentsum=0
        for i in self._cardsarrayhand:
            self._currentsum+=i.get_value()
        if self._currentsum > 21:
            print('ALIARM FOR USER!!!exceeds 21!!! Checking for Tuz in the hand is starting!')
            if self.tuz_checker():
                print('No Tuz, and currentsum',self._currentsum,'in the',player_name,'hand exceeds the threshold value "21" and he lost','\n\n')
                self._stoptakecard=True
            else:print('The currentsum in the',player_name,'hand is',self._currentsum,'\n\n')
        else:print('The currentsum in the',player_name,'hand is',self._currentsum,'\n\n')
    def tuz_checker(self):
            count_of_tuz=0
            for i in self._cardsarrayhand:
                if i.change_values_for_T():
                    self._currentsum-=10
                    count_of_tuz+=1
                    break                             #if in the deck more than 1 Tuz
            if count_of_tuz==0:return 1
    def show_current_hand(self,player_name):
        for i in self._cardsarrayhand:
            print('The card "',i,'" is in the',player_name,'hand')
        self.set_currentsum(player_name)
    def get_stoptakecard(self):
        return self._stoptakecard
    def get_currentsum(self):
        return self._currentsum

class bot(hand):
    def add_card(self,player_name,card):
        if self._stoptakecard:print('The Game is over for',player_name,'\n\n')
        elif self._stoptakecardbot:self.set_currentsum(player_name)
        else:
            self._cardsarrayhand.append(card) # берем карту в руку!!!проверить
            self.show_current_hand(player_name)
    def set_currentsum(self,player_name):
        self._currentsum=0
        for i in self._cardsarrayhand:
            self._currentsum+=i.get_value()
        if self._currentsum > 21:
            print('ALIARM FOR USER!!!exceeds 21!!! Checking for Tuz in the hand is starting!')
            if self.tuz_checker():
                print('No Tuz, and the currentsum',self._currentsum,'in the',player_name,'hand exceeds the threshold value "21" and he lost','\n\n')
                self._stoptakecard=True
            else:print('The currentsum in the',player_name,'hand is',self._currentsum,'\n\n')
        elif self._currentsum >= 17:
            print("The currentsum in the",player_name,"hand is",self._currentsum,"and he won't take the next card")
            self._stoptakecardbot=True
        else:print('The currentsum in the',player_name,'hand is',self._currentsum,'\n\n')

deck1=deck()
deck1.shuffler()
player1=hand()
bot_hand=bot()

def want_card():
    print("Do you want to get a card?")
    inp2=input()
    while inp2!='y' and inp2!='n':
        print('You should write "y" or "n"')
        inp2=input()
    if inp2=='y':return 1
    elif inp2=='n':return 0
def lose(player_name):
    print(player_name,'has lost!')
i=1
while not player1.get_stoptakecard() and want_card():
        player1.add_card('player_1',deck1.get_card())
        if i==1:
            player1.add_card('player_1',deck1.get_card())
            i=0
        bot_hand.add_card('bot',deck1.get_card())
        if player1.get_currentsum() > 21:
            lose(player1)
        elif bot_hand.get_currentsum() > 21:
            lose(bot_hand)





print("Exit from the game: at least one participant don't want to play or exceedingy value happens")
# deck1.show_current_deck()
# bot_hand.add_card('bot',deck1.get_card())


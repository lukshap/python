end = True
while end:
    print('Do you want to type the number(yes/no):')
    c = input()
    if c == 'yes':
        print('Please, type the number:')
        a = int(input())
        if a < 0:
            print('Negative number')
        elif a == 0:
            print('number is zero')
        elif a % 2 == 0:
            print('Even number')
        elif a % 2 == 1:
            print('odd number')
    elif c == 'no':
        print('OK,see you later')
        end = False
    else:
        print('Please, type "yes" or "no"')
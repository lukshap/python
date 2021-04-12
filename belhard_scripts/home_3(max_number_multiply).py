lst = []
for i in open('matrix.txt'):
    #print(i.rstrip().split(' '))
    lst.append(i.rstrip().split(' '))
#print(lst)
for each in range(20):
    for each2 in range(20):
        lst[each][each2] = int(lst[each][each2])
def main(lst,n):
    #print(lst)
    def horizontal(lst,n):
        max = lst[0][0]
        for i in lst:
            for j in range((len(lst[0])-n)+1):
                rez=i[j]
                for k in range (1,n):
                    rez*=i[j+k]
                if max<rez:max=rez
        return max
    #print(horizontal(lst,n))
    a=horizontal(lst,n)

    def vertical(lst,n):
        max = lst[0][0]
        for j in range(len(lst[0])):
            for i in range((len(lst[0])-n)+1):
                rez=1
                for k in range(n):
                    rez*=lst[i+k][j]
                if max<rez:max=rez
        return max
    #print(vertical(lst,n))
    if a<vertical(lst,n):a=vertical(lst,n)
    def pr_diagonal(lst,n):
        max=lst[0][0]
        for i in range((len(lst)-n)+1):
            for j in range((len(lst[0])-n)+1):
                rez=1
                for k in range(n):
                    rez*=lst[i+k][j+k]
                if max<rez:max=rez
        return max
    #print(pr_diagonal(lst,n))
    if a<pr_diagonal(lst,n):a=pr_diagonal(lst,n)
    def obr_diagonal(lst,n):
        max=lst[0][0]
        for i in range((len(lst)-n)+1):
            for j in range(-(len(lst[0])-n+1),0):
                rez=1
                for k in range(n):
                    rez*=lst[i+k][j-k]
                if max<rez:max=rez
        return max
    #print(obr_diagonal(lst,n))
    if a<obr_diagonal(lst,n):a=obr_diagonal(lst,n)
    return a
print(main(lst,int(input())))
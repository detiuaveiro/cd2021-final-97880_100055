PASSWORD_SIZE = 2

def mergeList(listt):
    '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
    listt.sort()
    changed = True
    while changed:
        changed = False
        #print("List len:",len(listt))
        for i in range(1,len(listt)):
            #print("Checking:", i, i-1)
            if rangeOverlaps(listt[i],listt[i-1]):
                maxR = max(listt[i][1],listt[i-1][1])
                newRange = [listt[i-1][0], maxR]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
            # if listt[i-1] == listt[i]:
            #     del listt[i]
            #     changed = True
            #     listt.sort()
            #     break
            elif listt[i-1][1]+1 == listt[i][0]:
                newRange = [listt[i-1][0], listt[i][1]]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
            # elif listt[i][1] > listt[i-1][1] >= listt[i][0]:
            #     newRange = [listt[i-1][0], listt[i][1]]
            #     del listt[i-1]
            #     del listt[i-1]
            #     listt.append(newRange)
            #     changed = True
            #     listt.sort()
            #     break
            # elif listt[i][1] < listt[i-1][1]:
            #     del listt[i]
            #     changed = True
            #     listt.sort()
            #     break
    return listt

def invertRangeList(listt):
    listt = mergeList(listt)
    MAX = 62**PASSWORD_SIZE
    print("MAX:",MAX)
    if len(listt) == 0: return [0, MAX]
    elif len(listt) == 1:
        if listt[0][0] == 0: return [[listt[0][1]+1, MAX]]
        elif listt[0][1] == MAX: return [[0, listt[0][0]-1]]
        else: return[[0,listt[0][0]-1],[listt[0][1]+1,MAX]]
    else:
        newlistt = []
        for i in range(len(listt)):
            if i == 0:
                if listt[i][0] == 0: continue
                else: newlistt.append([0, listt[i][0]-1])
            else:
                newlistt.append([listt[i-1][1]+1,listt[i][0]-1])
                if i == len(listt)-1: 
                    if not listt[i][1] == MAX:
                        newlistt.append([listt[i][1]+1,MAX])  
    return newlistt

def rangeOverlaps(r1 : list, r2 : list):
        if r1[0] <= r2[1] and r1[1] >= r2[0]: return True
        else: return False

def contains(r1 : list, r2 : list):
    if r1[0]<=r2[0] and r2[1]<=r1[1]:
        return True
    return False

r1 = [10,20]
r2 = [10,20]
print(contains(r1,r2))

# testlist = [[0,465],[122,122]]
# testlist.sort()

# print(testlist)
# testlist=mergeList(testlist)

# print(testlist)
# testlist=mergeList(testlist)
# print(testlist)
# testlist =invertRangeList(testlist)
# print(testlist)





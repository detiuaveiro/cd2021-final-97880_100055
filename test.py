PASSWORD_SIZE = 3

def mergeList(list):
    '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
    list.sort()
    changed = True
    while changed:
        changed = False
        for i in range(len(list)):
            if i == 0:
                continue
            if list[i-1][1]+1 == list[i][0]:
                newRange = [list[i-1][0], list[i][1]]
                del list[i-1]
                del list[i-1]
                list.append(newRange)
                changed = True
                list.sort()
                break
            elif list[i][1] > list[i-1][1] >= list[i][0]:
                newRange = [list[i-1][0], list[i][1]]
                del list[i-1]
                del list[i-1]
                list.append(newRange)
                changed = True
                list.sort()
                break
            elif list[i][1] < list[i-1][1]:
                del list[i]
                changed = True
                list.sort()
                break
    return list

def invertRangeList(list):
    list = mergeList(list)
    MAX = 62**PASSWORD_SIZE-1
    if len(list) == 0:
        return [0, MAX]
    elif len(list) == 1:
        if list[0][0] == 0:
            return [list[0][1]+1, MAX]
        elif list[0][1] == MAX:
            return [0, list[0][0]-1]
    else:
        newList = []
        for i in range(len(list)):
            if i == 0:
                if list[i][0] == 0:
                    continue
                else:
                    newList.append([0, list[i][0]])
                continue
            if i == len(list)-1:
                if list[i][1] == MAX:
                    continue
                else:
                    newList.append([list[i][1],MAX])
            newList.append([list[i-1][1]+1,list[i][0]-1])
    newList.sort()
    return newList

testlist = [[300,62**PASSWORD_SIZE-1],[400,500]]
testlist.sort()

print(testlist)
mergeList(testlist)
print(testlist)

print(invertRangeList(testlist))



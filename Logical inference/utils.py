def add(x, x_dict, _tuple):
    if x not in x_dict:
        x_dict[x] = set()
    x_dict[x].add(_tuple)

def extract_single(x_dict):
    ans = set()
    for k, v in x_dict.items():
        if len(v) == 1:
            ans.update(v)
    return ans

def extract_multi(x_dict):
    ans = set()
    for k, v in x_dict.items():
        if len(v) >= 2:
            ans.update(v)
    return ans

# x claims that he/she doesn't know, but x is sure that y doesn't know either
# x's number leads to multiple choices
# and these multiple choices are also y's multiple choices
def both_multi(x_dict, y_dict):
    ans = set()
    for k, v in x_dict.items():
        if len(v) >= 2:
            flag = True
            for _tuple in v:
                if _tuple in extract_single(y_dict):
                    flag = False
                    break
            if flag:
                ans.update(v)
    return ans

# update the given dictionary by common knowledge (candidate set) by now
def update(x_dict, candidate):
    # for k, v in x_dict.items():
    for k in list(x_dict.keys()):
        # v = x_dict[k]
        # for _tuple in v:
        #     if _tuple not in candidate:
        #         v.remove(_tuple)
        x_dict[k] &= candidate
        if len(x_dict[k]) == 0:
            del(x_dict[k])
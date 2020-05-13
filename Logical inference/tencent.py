# English Version:
# Tencent interview questions
# 1-20 The two numbers tell the sum to A and the product to B,
# A said: I don't know,
# B also said: I don’t know,
# A said: now I know,
# B went on to say: now I also know,
# Ask: what are these two numbers?
# Consider two situations: a and b may be the same and may not be the same
# 
# Chinese Version:
# 腾讯面试题
# 1-20的两个数把和告诉A,积告诉B，
# A说不知道是多少，
# B也说不知道，
# 这时A说我知道了，
# B接着说我也知道了，
# 问这两个数是多少？
# 考虑两种可能：a与b可能相同和不可能相同
from utils import add, extract_multi, extract_single, both_multi, update

p_dict = {}
q_dict = {}
for a in range(1,20+1):
    for b in range(a,20+1):
        p = a+b
        add(p, p_dict, (a,b))
        q = a*b
        add(q, q_dict, (a,b))
# p claims that he/she doesn't know:
candidate = extract_multi(p_dict)
update(p_dict, candidate)
update(q_dict, candidate)
print('p claims that he/she doesn\'t know: ', candidate)
print('-----------------------')
# q claims that he/she doesn't know:
candidate &= extract_multi(q_dict)
update(p_dict, candidate)
update(q_dict, candidate)
print('q claims that he/she doesn\'t know: ', candidate)
print('-----------------------')
# p claims that he/she knows
candidate &= extract_single(p_dict)
update(p_dict, candidate)
update(q_dict, candidate)
print('p claims that he/she knows: ', candidate)
print('-----------------------')
# q claims that he/she knows:
candidate &= extract_single(q_dict)
update(p_dict, candidate)
update(q_dict, candidate)
print('q claims that he/she knows: ', candidate)
print('-----------------------')
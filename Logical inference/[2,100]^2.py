# English Version:
# Take two numbers from 2-100, tell the sum to A, and tell the product to B,
# A to B said: I don’t know what these two numbers are, but I ’m sure you do n’t know either.
# B said: I didn't know it, but now I know.
# Jia said: Then I also know.
# What are these two numbers?
# 
# Chinese Version:
# 从2-100中取出两个数,把和告诉甲,把积告诉乙,
# 甲对乙说：我不知道这两个数是什么,但我肯定你也不知道.
# 乙说，我本来不知道，但现在知道了.
# 甲说：那我也知道了.
# 这两个数是多少？
from utils import add, extract_multi, extract_single, both_multi, update

p_dict = {}
q_dict = {}
for a in range(2,100+1):
    for b in range(a+1,100+1):
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
# p claims that q doesn't know:
candidate &= both_multi(p_dict, q_dict)
update(p_dict, candidate)
update(q_dict, candidate)
print('p claims that q doesn\'t know: ', candidate)
print('-----------------------')
# q claims that he/she knows:
candidate &= extract_single(q_dict)
print('q claims that he/she knows: ', candidate)
print('-----------------------')
update(p_dict, candidate)
update(q_dict, candidate)
# p claims that he/she knows:
candidate &= extract_single(p_dict)
print('p claims that he/she knows: ', candidate)
print('-----------------------')
update(p_dict, candidate)
update(q_dict, candidate)
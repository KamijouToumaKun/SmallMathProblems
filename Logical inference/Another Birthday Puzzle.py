# English Version:
# Xiaoming and Xiaoqiang are both students of Teacher Zhang.
# Mr. Zhang's birthday is on a certain day of the month, and neither of them knows Mr. Zhang's birthday.
# Birthday is a day in the following 10 groups:
# March 4 March 5 March 8
# June 4 June 7
# September 1 September 5
# December 1 December 2 December 8
# Teacher Zhang told Xiaoming about the month M and Xiaoqiang about the day N. Teacher Zhang asked them if they knew his birthday?
# Xiaoming said: I don't know, but Xiaoqiang certainly doesn't know either.
# Xiaoqiang said: I didn't know it, but now I know.
# Xiaoming said: Then I also know.
# Based on the above dialogue, please deduce which day is Teacher Zhang's birthday?

# Chinese Version:
# 小明和小强都是张老师的学生,张老师的生日是某月某日,2人都不知道张老师的生日.
# 生日是下列10组中一天：
# 3月4日 3月5日 3月8日
# 6月4日 6月7日
# 9月1日 9月5日
# 12月1日 12月2日 12月8日
# 张老师把月份M告诉了小明,把日子N告诉了小强,张老师问他们知道他的生日是那一天吗?
# 小明说：我不知道,但小强肯定也不知道。
# 小强说：本来我也不知道,但是现在我知道了。
# 小明说：那我也知道了。
# 请根据以上对话推断出张老师 生日是哪一天？
from utils import add, extract_multi, extract_single, both_multi, update

p_dict = {}
q_dict = {}
candidate = [(3,4),(3,5),(3,8),(6,4),(6,7),(9,1),(9,5),(12,1),(12,2),(12,8)]
for a, b in candidate:
    p = a
    add(p, p_dict, (a,b))
    q = b
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
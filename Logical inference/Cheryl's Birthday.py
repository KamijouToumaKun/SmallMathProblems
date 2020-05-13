# The question is number 24 in a list of 25 questions, and reads as follows:[4]
# May		15	16			19
# June				17	18	
# July	14		16			
# August	14	15		17		
# 
# Cheryl then tells Albert and Bernard separately the month and the day of her birthday respectively.

# Albert: I don't know when Cheryl's birthday is, but I know that Bernard doesn't know too. [sic]
# Bernard: At first I don't [sic] know when Cheryl's birthday is, but I know now.
# Albert: Then I also know when Cheryl's birthday is.
# So when is Cheryl's birthday?"
from utils import add, extract_multi, extract_single, both_multi, update

p_dict = {}
q_dict = {}
candidate = [(5,15),(5,16),(5,19),(6,17),(6,18),(7,14),(7,16),(8,14),(8,15),(8,17)]
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
# Nim游戏的增强版，但是双方能报的数有次数限制，1～8分别只能报4次，得39胜，超过39输

GOAL = 39
CARD_NUMBER = 4

import numpy as np
dp = -np.ones((CARD_NUMBER+1,)*8, dtype=np.int32) # 还剩的牌
cards = range(1,8+1)
# 状态数 5^8
# 	4 4 4 4 4 4 4 4
# *	1 2 3 4 5 6 7 8

def get_sum(rests):
	return np.dot(CARD_NUMBER-rests, cards)

def get_dp(rests, get_scheme=False):
	if get_scheme or dp[tuple(rests)] == -1: # 没有计算与存储过dp
		if get_sum(rests) > GOAL: dp[tuple(rests)] = 1 # 已经打的牌超过了goal，先手胜利，因为是对方爆掉
		elif get_sum(rests) == GOAL: dp[tuple(rests)] = 0 # 已经打的牌等于goal，先手失败，因为是对方刚好
		else:
			ans = 1
			for j in range(8):
				if rests[j] >= 1:
					rests[j] -= 1
					ans = get_dp(rests)
					rests[j] += 1 # 恢复
					if ans == 0:
						break
			if ans == 0:
				dp[tuple(rests)] = 1 # 只要有一个j使得dp[rests-j]=0: 交换后后手必胜，则当前为先手必胜
				if get_scheme: scheme = j
			else:
				dp[tuple(rests)] = 0 # 否则为后手必胜
				if get_scheme: scheme = -1

	if get_scheme: return dp[tuple(rests)], scheme
	else: return dp[tuple(rests)]

def is_illegal(player, rests):
	return not player.isdigit() or int(player) not in range(1,8+1) \
		or rests[int(player)-1] == 0 or get_sum(rests)+cards[int(player)-1] > GOAL

if __name__ == '__main__':
	rests = np.zeros((8,), dtype=np.int32)
	for rests[0] in range(CARD_NUMBER+1):
		for rests[1] in range(CARD_NUMBER+1):
			for rests[2] in range(CARD_NUMBER+1):
				for rests[3] in range(CARD_NUMBER+1):
					for rests[4] in range(CARD_NUMBER+1):
						for rests[5] in range(CARD_NUMBER+1):
							for rests[6] in range(CARD_NUMBER+1):
								for rests[7] in range(CARD_NUMBER+1):
									get_dp(rests)

	while True:
		ans, scheme = get_dp(rests, get_scheme=True)
		rests[scheme] -= 1
		print('Computer\'s move: ', scheme+1, 'rest cards: ', rests, 'sum: ', get_sum(rests))
		print('Your move: ')
		player = input()
		while is_illegal(player, rests):
			print('Invalid move!')
			player = input()
		rests[int(player)-1] -= 1
		print('Your move: ', player, 'rest cards: ', rests, 'sum: ', get_sum(rests))
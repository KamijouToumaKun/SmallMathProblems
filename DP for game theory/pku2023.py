# (2023北大金秋营)甲乙两人在一张初始空白的黑板上玩游戏，
# 由甲开始，他们轮流在黑板上写大于1的整数，要求每次写的数不能是黑板上已有数的自然数系数线性组合，
# 第一个不能继续写的人输掉游戏，问：谁有必胜策略？

import numpy as np
dp = -np.ones((2,)*(20+1), dtype=np.int32)
# 状态数 2^20

def set_flag(flags, i):
	flags = flags.copy()

	for a in range(1,20+1):
		if a*i <= 20:
			flags[a*i] = True
			for j in range(2,20+1):
				if flags[j]:
					if a*i + j <= 20:
						flags[a*i+j] = True
					else:
						break
					# a*i + b*j = True, a=1,2,..., b=0,1,...
					# TODO: 存储一个 blackboard = [] 会更方便，不需要遍历那么多，只需要每来一个新数都跟前面数组合一下
		else:
			break

	return flags	

def get_dp(flags, get_scheme=False):
	if get_scheme or dp[tuple(flags)] == -1: # 没有计算与存储过dp
		ans = 1
		for i in range(2,20+1):
			if not flags[i]: # 这个位置还可以用
				new_flags = set_flag(flags, i)
				ans = get_dp(new_flags)
				if ans == 0:
					break
		if ans == 0:
			dp[tuple(flags)] = 1 # 只要有一个j使得dp[new_flags]=0: 交换后后手必胜，则当前为先手必胜
			if get_scheme: scheme = i
		else:
			dp[tuple(flags)] = 0 # 否则为后手必胜，也包括找不到地方填写的情况
			if get_scheme: scheme = -1

	if get_scheme: return dp[tuple(flags)], scheme
	else: return dp[tuple(flags)]

def is_illegal(player, flags):
	return not player.isdigit() or int(player) not in range(2,20+1) or flags[int(player)]

if __name__ == '__main__':
	flags = np.zeros((20+1,), dtype=np.int32)
	flags[0] = flags[1] = 1 # 0和1不用填
	for flags[2] in range(1,-1,-1):
		for flags[3] in range(1,-1,-1):
			for flags[4] in range(1,-1,-1):
				for flags[5] in range(1,-1,-1):
					for flags[6] in range(1,-1,-1):
						for flags[7] in range(1,-1,-1):
							for flags[8] in range(1,-1,-1):
								for flags[9] in range(1,-1,-1):
									for flags[10] in range(1,-1,-1):
										for flags[11] in range(1,-1,-1):
											for flags[12] in range(1,-1,-1):
												for flags[13] in range(1,-1,-1):
													for flags[14] in range(1,-1,-1):
														for flags[15] in range(1,-1,-1):
															for flags[16] in range(1,-1,-1):
																for flags[17] in range(1,-1,-1):
																	for flags[18] in range(1,-1,-1):
																		for flags[19] in range(1,-1,-1):
																			for flags[20] in range(1,-1,-1):
																				get_dp(flags)

	while True:
		ans, scheme = get_dp(flags, get_scheme=True)
		flags = set_flag(flags, scheme)
		print('Computer\'s move: ', scheme, 'flags: ', flags)
		print('Your move: ')
		player = input()
		while is_illegal(player, flags):
			print('Invalid move!')
			player = input()
		flags = set_flag(flags, int(player))
		print('Your move: ', player, 'flags: ', flags)
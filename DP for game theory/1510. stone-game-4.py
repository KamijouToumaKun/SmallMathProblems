# 1510. 石子游戏4：每个人可以取完全平方数块石头。布尔类型的必胜策略
class Solution:
    def winnerSquareGame(self, n: int) -> bool:
        # dp[0] = False
        # dp[n] = True if any{dp[n-i^2] == False}
        dp = [False for i in range(n+1)]
        for i in range(1, n+1):
            for x in range(1, int(sqrt(i))+1): # x <= int(sqrt(i)) <= sqrt(i)
                if dp[i-x*x] == False:
                    dp[i] = True # 只要我有一种方法让后手必败
                    break # 就是先手必胜
            # 否则就是先手必败
        return dp[n]

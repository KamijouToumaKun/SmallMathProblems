# 1406. 石子游戏3：每个人可以取靠前的最多三堆石头。零和博弈，负极大值算法，倒推
class Solution:
    def stoneGameIII(self, stoneValue: List[int]) -> str:
        # dp[0] = max{
        # dp[0][1] = stoneValue[0] - max{dp[1][]}
        # dp[0][2] = stoneValue[0~1] - max{dp[2][]}
        # dp[0][3] = stoneValue[0~2] - max{dp[3][]}
        # }
        # 即：
        # dp[i] = max(
        #     stoneValue[i] - dp[i+1], 
        #     stoneValue[i] + stoneValue[i+1] - dp[i+2],
        #     stoneValue[i] + stoneValue[i+1] + stoneValue[i+2] - dp[i+3] 
        # )
        dp = [0 for _ in range(len(stoneValue)+3)]
        for i in range(len(stoneValue)-1, -1, -1):
            dp[i] = stoneValue[i] - dp[i+1]
            if i+1 < len(stoneValue):
                dp[i] = max(dp[i], stoneValue[i] + stoneValue[i+1] - dp[i+2])
            if i+2 < len(stoneValue):
                dp[i] = max(dp[i], stoneValue[i] + stoneValue[i+1] + stoneValue[i+2] - dp[i+3])
                
        if dp[0] > 0: return "Alice"
        elif dp[0] == 0: return "Tie"
        else: return "Bob"

# https://leetcode.cn/problems/chalkboard-xor-game/description/
# 但是为什么呢？？？
class Solution:
    def xorGame(self, nums: List[int]) -> bool:
        # return sum(nums)==0 ? 先手 : len(nums)%2==0，不需要排除0元素
        ans = 0
        # count = 0
        for num in nums:
            ans ^= num
            # count += (num != 0)
        if ans == 0:
            return True
        else:
            # return count%2 == 0
            return len(nums)%2 == 0

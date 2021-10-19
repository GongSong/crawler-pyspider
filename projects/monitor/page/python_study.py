
# nums = [1,1,2,2,3,3,3,4,4,4,5]
nums = [1,2,2]

def removeDuplicates(nums):
    """
    :type nums: List[int]
    :rtype: int
    """
    fast = 0
    while True:
        n = len(nums)
        if fast >= n - 2:
            break
        if n <= 1:
            break
        if nums[fast] == nums[fast + 1]:
            del nums[fast]
            fast -= 1

        fast += 1
    return len(nums)

print(removeDuplicates(nums))
a = [4,5,4,1,3,4,5,6,7,9,1]
b = []
def bubble_sort(arr):
    n = len(arr)
    # 外层循环控制排序轮数
    for i in range(n):
        # 内层循环控制每轮比较次数
        for j in range(0, n-i-1):
            # 相邻元素比较，若逆序则交换
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
b = bubble_sort(a)
print(b)

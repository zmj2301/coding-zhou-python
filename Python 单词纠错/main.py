from typing import TypeAlias

def build_lexicon(filename:str) -> set[str]:
    """从给定文件中构建单词集"""
    lexicon = set()
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            # 移除所有标点符号和多余空格
            # 先转为小写
            line = line.strip().lower()
            # 移除所有标点符号
            for punct in ',.!?;:"()[]{}_-*&^%$#@~|\\/<>':
                line = line.replace(punct, '')
            # 分割单词
            words = line.split()
            # 更新单词集
            lexicon.update(words)
    return lexicon

WordInfo: TypeAlias = tuple[str, int,int]

def edit_distance(s1:str,s2:str) -> int:
    """计算两个字符串的编辑距离"""
    m, n = len(s1), len(s2)
    # 创建dp数组，dp[i][j]表示s1前i个字符与s2前j个字符的编辑距离
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 初始化第一行和第一列
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # 填充dp数组
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                # 当前字符相同，不需要操作
                dp[i][j] = dp[i-1][j-1]
            else:
                # 取插入、删除、替换的最小值+1
                dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])
    
    return dp[m][n]

def most_similar_word(s:str,lexicon:set[str]) -> str:
    """找到最相似的单词"""
    if s in lexicon:
        return s
    min_steps = float("inf")
    target = ""
    for word in lexicon:
        step = edit_distance(s,word)
        if step < min_steps:
            min_steps = step
            target = word
    return target

def scan_words(filename:str) -> list[WordInfo]:
    """从给定文件中扫描单词"""
    words = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        num = 0
        # 记录第几行
        for line in file:
            num += 1
            # 移除所有标点符号和多余空格
            # 先转为小写
            line = line.lower()
            # 移除所有标点符号
            for punct in ',.!?;:"()[]{}_-*&^%$#@~|\\/<>':
                line = line.replace(punct, '')
            # 分割并去除空字符串
            line_words = line.split()
            
            # 更新单词集
            for i, word in enumerate(line_words):
                # 记录第几个单词
                words.append((word, num, i+1))
    return words

if __name__ == '__main__':
    lexicon = build_lexicon('words_alpha.txt')
    words = scan_words('text.txt')
    print("以下单词可能写错了：")
    print("-----------------")
    for word in words:
        text,line,col = word
        if text not in lexicon:
            suggest = most_similar_word(text,lexicon)
            print(f"第{line}行第{col}个单词{text}，你可能想输入：{suggest}")


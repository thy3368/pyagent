import numpy as np
from collections import defaultdict

class SimpleLLM:
    def __init__(self):
        self.vocab = {}  # 词汇表
        self.reverse_vocab = {}  # 反向词汇表
        self.transitions = defaultdict(lambda: defaultdict(int))  # 转移概率矩阵
        self.word_freq = defaultdict(int)  # 词频统计
    
    def tokenize(self, text):
        """简单分词"""
        return text.lower().split()
    
    def build_vocab(self, texts):
        """构建词汇表"""
        words = set()
        for text in texts:
            words.update(self.tokenize(text))
        
        self.vocab = {word: idx for idx, word in enumerate(sorted(words))}
        self.reverse_vocab = {idx: word for word, idx in self.vocab.items()}
    
    def train(self, texts):
        """训练模型：统计词频和转移概率"""
        self.build_vocab(texts)
        
        for text in texts:
            tokens = self.tokenize(text)
            # 统计词频
            for token in tokens:
                self.word_freq[self.vocab[token]] += 1
            
            # 统计转移概率
            for i in range(len(tokens) - 1):
                curr_idx = self.vocab[tokens[i]]
                next_idx = self.vocab[tokens[i + 1]]
                self.transitions[curr_idx][next_idx] += 1
        
        # 计算概率
        for curr_idx in self.transitions:
            total = sum(self.transitions[curr_idx].values())
            for next_idx in self.transitions[curr_idx]:
                self.transitions[curr_idx][next_idx] /= total
    
    def generate(self, start_word, length=5):
        """生成文本"""
        if start_word not in self.vocab:
            return "起始词不在词汇表中"
        
        result = [start_word]
        current_idx = self.vocab[start_word]
        
        for _ in range(length - 1):
            if current_idx not in self.transitions:
                break
                
            # 根据转移概率选择下一个词
            next_words = list(self.transitions[current_idx].keys())
            probabilities = list(self.transitions[current_idx].values())
            
            next_idx = np.random.choice(next_words, p=probabilities)
            result.append(self.reverse_vocab[next_idx])
            current_idx = next_idx
        
        return " ".join(result)

# 示例使用
if __name__ == "__main__":
    # 训练数据
    training_texts = [
        "我 喜欢 机器学习",
        "机器学习 很 有趣",
        "深度学习 是 机器学习 的 一部分",
        "我 正在 学习 深度学习",
        "机器学习 需要 大量 数据"
    ]
    
    # 初始化并训练模型
    llm = SimpleLLM()
    llm.train(training_texts)
    
    # 生成文本
    print("\n生成的文本示例：")
    start_words = ["机器学习", "我", "深度学习","唐红尧"]
    for word in start_words:
        generated = llm.generate(word, length=4)
        print(f"起始词 '{word}': {generated}")
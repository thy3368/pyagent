import openai
import os

class SimpleAgent:
    def __init__(self, name="AI Assistant", system_prompt=None):
        self.name = name
        self.conversation_history = []
        self.system_prompt = system_prompt or f"你是一个名叫 {self.name} 的助手。你应该简洁专业地回答问题。"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
    
    def think(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # 调用 OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            # 保存 AI 的回复到历史记录
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
        except Exception as e:
            return f"抱歉，发生了错误: {str(e)}"
    
    def run(self):
        print(f"{self.name} 已启动，输入 '退出' 结束对话")
        
        while True:
            user_input = input("你: ")
            if user_input.lower() == "退出":
                print(f"{self.name}: 再见！")
                break
            
            response = self.think(user_input)
            print(f"{self.name}: {response}")

if __name__ == "__main__":
    system_prompt = """你是一个专业的编程助手。你应该：
    1. 提供简洁清晰的代码示例
    2. 解释技术概念时使用类比
    3. 始终考虑代码的最佳实践
    4. 主动指出潜在的问题和优化方向"""
    
    agent = SimpleAgent(name="编程助手", system_prompt=system_prompt)
    agent.run()
from openai import OpenAI
import json

class SimpleAgent:
    def __init__(self, name="AI Assistant", system_prompt=None):
        self.name = name
        self.conversation_history = []
        self.system_prompt = system_prompt or f"""你是一个名叫 {self.name} 的助手。
你需要按照以下步骤思考和回答：
1. 思考 (Thought)：分析用户的问题和需求
2. 行动 (Action)：确定需要采取的具体行动
3. 观察 (Observation)：评估行动的结果
4. 回答 (Response)：根据观察给出最终答案

请以 JSON 格式输出你的思考过程，格式如下：
{{
    "thought": "你的分析思考",
    "action": "需要采取的行动",
    "observation": "行动后的观察",
    "response": "最终回答"
}}"""
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )

    def think(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})

            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content
            
            # 尝试解析 JSON 响应
            try:
                thought_process = json.loads(ai_response)
                formatted_response = f"""思考过程：{thought_process['thought']}
执行动作：{thought_process['action']}
观察结果：{thought_process['observation']}
最终回答：{thought_process['response']}"""
                self.conversation_history.append({"role": "assistant", "content": formatted_response})
                return formatted_response
            except json.JSONDecodeError:
                # 如果无法解析为 JSON，直接返回原始响应
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
    sql_system_prompt = """你是一个专业的 SQL 助手。你的主要职责是：
    1. 将自然语言转换为准确的 SQL 查询语句
    2. 解释 SQL 查询的执行逻辑
    3. 提供优化建议
    4. 确保生成的 SQL 遵循最佳实践
    5. 对复杂查询提供分步解释
    
    规则：
    1. 始终使用标准 SQL 语法
    2. 查询语句要格式化和缩进
    3. 对于复杂查询，提供注释说明
    4. 如果需要表结构信息，要主动询问用户"""

    agent = SimpleAgent(name="SQL助手", system_prompt=sql_system_prompt)
    agent.run()

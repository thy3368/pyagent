from openai import OpenAI


class Text2SQLAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        self.conversation_history = []
        self.system_prompt = """你是一个专业的 SQL 转换助手。职责：
1. 将自然语言精确转换为 SQL
2. 解释查询逻辑
3. 提供优化建议
4. 对复杂查询提供注释
5. 主动询问所需的表结构信息"""

    def generate_sql(self, user_input: str) -> str:
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

            sql_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": sql_response})
            return sql_response

        except Exception as e:
            return f"生成 SQL 时发生错误: {str(e)}"

    def run(self):
        print("SQL 转换助手已启动，输入 '退出' 结束程序")

        while True:
            user_input = input("\n请描述你的查询需求: ")
            if user_input.lower() == "退出":
                print("再见！")
                break

            response = self.generate_sql(user_input)
            print("\nSQL 转换结果：")
            print("----------------------------------------")
            print(response)
            print("----------------------------------------")


if __name__ == "__main__":
    agent = Text2SQLAgent()
    agent.run()

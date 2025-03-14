from openai import OpenAI
import json
from typing import List, Dict, Any
import base64

class SimpleAgent:
    def __init__(self, name="AI Assistant", system_prompt=None):
        self.name = name
        self.conversation_history = []
        self.system_prompt = system_prompt or f"你是一个名叫 {self.name} 的助手。"
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        self.available_functions = {
            "get_current_weather": self.get_current_weather,
            "calculate": self.calculate,
        }
        self.available_functions.update({
            "image_to_vue": self.image_to_vue,
        })
    
    def image_to_vue(self, image_path: str, component_name: str = "GeneratedComponent") -> str:
        """将图片转换为 Vue 组件"""
        try:
            # 读取图片并转换为 base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 调用 Vision API 分析图片
            vision_response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请分析这张图片并生成对应的 Vue 3 组件代码，使用 Composition API"},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{image_data}"
                            }
                        ]
                    }
                ]
            )
            return vision_response.choices[0].message.content
        except Exception as e:
            return f"图片转换错误：{str(e)}"

    def get_functions_config(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_current_weather",
                "description": "获取指定位置的当前天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "城市名称"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "温度单位"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "calculate",
                "description": "计算数学表达式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 1 + 2 * 3"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "image_to_vue",
                "description": "将图片转换为 Vue 组件代码",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "图片文件的路径"
                        },
                        "component_name": {
                            "type": "string",
                            "description": "生成的 Vue 组件名称"
                        }
                    },
                    "required": ["image_path"]
                }
            }
        ]

    def think(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                functions=self.get_functions_config(),
                temperature=0.7
            )

            message = response.choices[0].message

            # 处理函数调用
            if hasattr(message, 'function_call') and message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                if function_name in self.available_functions:
                    function_response = self.available_functions[function_name](**function_args)
                    
                    # 将函数调用结果添加到对话历史
                    self.conversation_history.append({
                        "role": "function",
                        "name": function_name,
                        "content": function_response
                    })
                    
                    # 让模型处理函数返回结果
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": function_response
                    })
                    
                    final_response = self.client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=0.7
                    )
                    
                    ai_response = final_response.choices[0].message.content
                else:
                    ai_response = f"抱歉，函数 {function_name} 不可用"
            else:
                ai_response = message.content

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

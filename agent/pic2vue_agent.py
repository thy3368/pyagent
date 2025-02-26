import base64

from openai import OpenAI


class Pic2VueAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )

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
                            {"type": "text",
                             "text": f"请分析这张图片并生成对应的 Vue 3 组件代码，组件名为 {component_name}。要求：\n1. 使用 Composition API\n2. 代码要规范、整洁\n3. 样式要精确还原设计图\n4. 添加必要的类型声明"},
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

    def run(self):
        print("图片转 Vue 助手已启动，输入 '退出' 结束程序")

        while True:
            image_path = input("请输入图片路径（或输入'退出'）: ")
            if image_path.lower() == "退出":
                print("再见！")
                break

            component_name = input("请输入组件名称（直接回车使用默认名称）: ").strip()
            if not component_name:
                component_name = "GeneratedComponent"

            response = self.image_to_vue(image_path, component_name)
            print("\n生成的 Vue 组件代码：")
            print("----------------------------------------")
            print(response)
            print("----------------------------------------\n")


if __name__ == "__main__":
    agent = Pic2VueAgent()
    agent.run()

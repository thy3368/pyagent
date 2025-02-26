from openai import OpenAI
import base64
import speech_recognition as sr
from PIL import Image
import io

class MultiModalAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        self.conversation_history = []
        
    def process_image(self, image_path: str) -> str:
        """处理图像输入"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请描述这张图片的内容"},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{image_data}"
                            }
                        ]
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"图像处理错误：{str(e)}"

    def process_audio(self, audio_path: str) -> str:
        """处理语音输入"""
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language='zh-CN')
                return self.process_text(f"语音输入：{text}")
        except Exception as e:
            return f"语音处理错误：{str(e)}"

    def process_text(self, text: str) -> str:
        """处理文本输入"""
        try:
            self.conversation_history.append({"role": "user", "content": text})
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个多模态助手，可以处理文本、图像和语音输入。"}
                ] + self.conversation_history,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            return f"文本处理错误：{str(e)}"

    def run(self):
        print("多模态助手已启动")
        print("支持的命令：")
        print("1. 'image:路径' - 处理图片")
        print("2. 'audio:路径' - 处理语音")
        print("3. 直接输入文本进行对话")
        print("输入 '退出' 结束程序")

        while True:
            user_input = input("\n请输入: ")
            if user_input.lower() == "退出":
                print("再见！")
                break

            if user_input.startswith("image:"):
                image_path = user_input[6:].strip()
                response = self.process_image(image_path)
            elif user_input.startswith("audio:"):
                audio_path = user_input[6:].strip()
                response = self.process_audio(audio_path)
            else:
                response = self.process_text(user_input)

            print("\n助手回复：")
            print("----------------------------------------")
            print(response)
            print("----------------------------------------")

if __name__ == "__main__":
    agent = MultiModalAgent()
    agent.run()
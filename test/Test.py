from Agent import Agent

agent = Agent('/path/to/internlm2-chat-20b')

response, _ = agent.text_completion(text='你好', history=[])
print(response)

response, _ = agent.text_completion(text='周杰伦是哪一年出生的？', history=_)
print(response)

response, _ = agent.text_completion(text='周杰伦是谁？', history=_)
print(response)

response, _ = agent.text_completion(text='他的第一张专辑是什么？', history=_)
print(response)

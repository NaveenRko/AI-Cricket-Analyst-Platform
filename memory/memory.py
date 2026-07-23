# from langchain_classic.memory import ConversationBufferMemory

# memory = ConversationBufferMemory(
#     return_messages=True
# )

from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=4, return_messages=True)

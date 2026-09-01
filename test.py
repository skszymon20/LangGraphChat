from agent import get_agent
from langchain_core.messages import SystemMessage, HumanMessage
from models import init_database


init_database()
agent = get_agent()
cfg = {
    "configurable": {
        "thread_id": "test_thread_id"
    }
}
# for msg_chunk, metadata in agent.stream(
#     # {'messages': [HumanMessage("Tell me today's news in AI.")]},
#     {'messages': [HumanMessage("Calculate 2 + 2.")]},
#     config=cfg,
#     stream_mode='messages'
# ):
#     if msg_chunk.content:
#         msg_chunk_content = msg_chunk.content
#         # print(msg_chunk_content)
#         # print("----------------")
#         assert len(msg_chunk_content) == 1, f"Expected 1 text chunk, got {len(msg_chunk_content)}"
#         assert 'text' in msg_chunk_content[0], f"Expected 'text' in chunk, got {msg_chunk_content[0]}"
#         text_content = msg_chunk_content[0]['text']
#         print(text_content, end='')# , flush=True)

# response = agent.invoke(
#     {'messages': [HumanMessage("Calculate 2 + 2.")]},
#     # {'messages': [HumanMessage("Tell me today's news in AI.")]},
#     config=cfg,
# )
# response_content = response['messages'][-1].content
# print("RAW response content:\n", response_content)
# print("---------------------------------")
# print("response_content[0]['text']:\n", response_content[0]['text'])
# print()

for chunk in agent.stream(
    # {'messages': [HumanMessage("Calculate 2 + 2.")]},
    {'messages': [HumanMessage("What is my name?")]},
    config=cfg,
    stream_mode="messages"  # Streams the message tokens as they are generated
):
    # Extract and print the content of the current chunk
    chunk_content = chunk[0].content
    if chunk_content:
        if len(chunk_content) == 1 and 'text' in chunk_content[0]:
            text_content = chunk_content[0]['text']
            print(text_content, end='', flush=True)
print()

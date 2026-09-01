import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
# import certifi
# os.environ["SSL_CERT_FILE"] = certifi.where()
# os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from tools import tools


load_dotenv()
Path("data").mkdir(exist_ok=True)

DEFAULT_MODEL = os.environ.get("GOOGLE_MODEL", "gemini-3.5-flash-lite")

ALLOWED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]

SYSTEM_PROMPT = """
You are a helpful assistant that can answer questions and perform tasks. You have access to the following tools:
- Calculator: You can perform calculations with a use of the calculator tool.
- Web Search: You can search the web for information with a use of the Tavily Search tool.
- RAG: You can search uploaded documents with a use of the RAG tool.
- Memory Tool: You can store and retrieve important user information with a use of the Memory tool. Recall memory when useful.

Rules:
- Always use the tools when appropriate.
- If a user asks about uploaded documents use search_uploaded_documents.
- If a user orders you to remember something, use remember_this.
- If a user asks you to recall something, use recall_memory.
- For math related questions, use the calculator.
- If a user asks you to search the web, use the web_search tool.
- When performing a web search, provide a summary of the results and cite the sources.
- If you are unsure about an answer, use the tools to find the information instead of guessing.
"""

def build_agent(model_name: str = DEFAULT_MODEL) -> StateGraph:
    if model_name not in ALLOWED_MODELS:
        raise ValueError(f"Model {model_name} is not allowed. Allowed models: {ALLOWED_MODELS}")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state: MessagesState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state['messages']
        resp = llm_with_tools.invoke(messages)
        return {
            'messages': [resp]
        }

    tool_node = ToolNode(tools)

    workflow = StateGraph(
        MessagesState
    )

    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "chatbot")
    workflow.add_conditional_edges("chatbot", tools_condition)
    workflow.add_edge("tools", "chatbot")

    conn = sqlite3.connect(
        'data/langgraph_ckpts.sqlite', check_same_thread=False
    )
    ckpter = SqliteSaver(conn)

    return workflow.compile(checkpointer=ckpter)

_AGENT_CACHE = {}

def get_agent(model_name: str | None = None) -> StateGraph:
    """
    Returns a cached agent instance for the specified model name.
    If the agent for the model name does not exist in the cache, it builds a new agent and caches it.
    If no model name is provided, it uses the default model.
    """
    if model_name is not None and model_name not in ALLOWED_MODELS:
        raise ValueError(f"Model {model_name} is not allowed. Allowed models: {ALLOWED_MODELS}")
    if model_name is None:
        model_name = DEFAULT_MODEL
    if model_name not in _AGENT_CACHE:
        _AGENT_CACHE[model_name] = build_agent(model_name)
    return _AGENT_CACHE[model_name]
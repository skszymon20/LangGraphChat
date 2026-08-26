import math
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from database import save_long_term_memory, search_long_term_memory
from rag import retrieve_from_rag


load_dotenv()

CURRENT_THREAD_ID = 'default'

def set_curr_thread_id(thread_id: str):
    global CURRENT_THREAD_ID
    CURRENT_THREAD_ID = thread_id

web_search = TavilySearch(
    max_results=3,
    topic="general",
    search_depth="advanced"
)

@tool
def calculator(expression: str) -> str:
    """
    A simple calculator tool that evaluates mathematical expressions.
    Example usage:
    >>> calculator("2 + 2")
    '4'
    >>> calculator("10 / 2")
    '5.0'
    >>> calculator("5 * 3 - 2")
    '13'
    >>> calculator("math.sqrt(16)")
    '4.0'
    """
    try:
        allowed_expressions = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum
        }
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": None}, allowed_expressions)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

@tool
def remember_this(info: str) -> str:
    """
    A tool to remember important information for future reference.
    Example usage:
    >>> remember_this("My favorite color is blue.")
    'Information saved successfully.'
    >>> remember_this("I have a meeting at 3 PM tomorrow.")
    'Information saved successfully.'
    """
    save_long_term_memory(CURRENT_THREAD_ID, info)
    return "Information saved successfully."

@tool
def recall_memory() -> str:
    """
    A tool to recall information from long-term memory.
    Example usage:
    >>> recall_memory()
    'My favorite color is blue.'
    >>> recall_memory()
    'I have a meeting at 3 PM tomorrow.'
    """
    return search_long_term_memory(CURRENT_THREAD_ID)


@tool
def search_uploaded_documents(query: str) -> str:
    """
    A tool to search uploaded documents using the RAG (Retrieval-Augmented Generation) system.
    Example usage:
    >>> search_uploaded_documents("What is the capital of France?")
    'The capital of France is Paris.'
    >>> search_uploaded_documents("Explain the theory of relativity.")
    'The theory of relativity, developed by Albert Einstein, consists of two main theories: special relativity and general relativity...'
    """
    return retrieve_from_rag(query, CURRENT_THREAD_ID)

tools = [calculator, web_search, remember_this, recall_memory, search_uploaded_documents]
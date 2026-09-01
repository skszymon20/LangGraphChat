from dotenv import load_dotenv
import os
import json
import uuid
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from agent import get_agent
from rag import add_doc_to_rag
from tools import set_curr_thread_id
from pydantic import BaseModel


load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates/")
Path("data").mkdir(exist_ok=True)
Path("data/rag_files").mkdir(exist_ok=True)
# init_database()

class ChatMessage(BaseModel):
    message: str

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={}  # NOTE following not working: {"title": "LangGraphChat", "welcome_msg": "Hello World! How can I help you today?"}
    )
@app.post("/chat")
def chat_endpoint(data: ChatMessage):
    # Simple reply logic. Replace with your AI pipeline.
    return {"reply": f"Echo: {data.message}"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)


#NOTE alternative version below:

# import uvicorn
# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel

# app = FastAPI()

# # Setup Jinja2 templates (looks for a templates folder, or current directory)
# templates = Jinja2Templates(directory="templates/")

# class ChatMessage(BaseModel):
#     message: str

# @app.get("/", response_class=HTMLResponse)
# def get_home(request: Request):
#     # Renders index.html using Jinja2 context variables
#     return templates.TemplateResponse(
#         request=request,
#         name="index.html",
#         context={"title": "Jinja2 AI Chat", "welcome_msg": "Hello World! How can I help you today?"}
#     )

# @app.post("/chat")
# def chat_endpoint(data: ChatMessage):
#     # Simple reply logic. Replace with your AI pipeline.
#     return {"reply": f"Echo: {data.message}"}

# if __name__ == "__main__":
#     # Runs the server locally on port 8000
#     uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

from dotenv import load_dotenv
import os
import json
import uuid
from pathlib import Path
import uvicorn
from fastapi import Depends, FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from agent import get_agent
from rag import add_doc_to_rag
from tools import set_curr_thread_id
from pydantic import BaseModel
from fastapi import status
from typing import Annotated, List
from database import get_db, Base, engine
from schemas import MessageResponse, MessageCreate, ThreadResponse, ThreadCreate
import models
from sqlalchemy.orm import Session
from sqlalchemy import select
from agent import get_agent


load_dotenv()
Base.metadata.create_all(bind=engine)
app = FastAPI()
templates = Jinja2Templates(directory="templates/")
Path("data").mkdir(exist_ok=True)
Path("data/rag_files").mkdir(exist_ok=True)

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

@app.get("/api/threads", response_model=List[ThreadResponse])
def get_threads(db: Annotated[Session, Depends(get_db)]):
    threads = db.execute(select(models.Thread)).scalars().all()
    return threads

@app.post("/api/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
def create_thread(thread: ThreadCreate, db: Annotated[Session, Depends(get_db)]):
    if not thread.title:
        title = thread.first_message[:50] + "..." if len(thread.first_message) > 50 else thread.first_message
    else:
        title = thread.title
    new_thread = models.Thread(
        id=str(uuid.uuid4()),
        title=title,
    )

    # Add the first message
    message = models.Message(
        thread_id=new_thread.id,
        role="user",
        content=thread.first_message
    )
    new_thread.messages.append(message)
    new_assistant_message = assistant_respond(message)
    new_thread.messages.append(new_assistant_message)
    
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    return new_thread

@app.get("/api/messages/{thread_id}", response_model=List[MessageResponse])
def get_messages(thread_id: str, db: Annotated[Session, Depends(get_db)]):
    messages = db.execute(
        select(models.Message).where(models.Message.thread_id == thread_id)
    ).scalars().all()
    return messages

def assistant_respond(message: models.Message):
    agent = get_agent()
    set_curr_thread_id(message.thread_id)
    cfg = {
        "configurable": {
            "thread_id": message.thread_id
        }
    }
    response = agent.invoke(
        {'messages': [HumanMessage(message.content)]},
        config=cfg,
    )
    response_content = response['messages'][-1].content
    if response_content and len(response_content) > 0 and 'text' in response_content[0]:
        assistant_reply = response_content[0]['text']
    else:
        assistant_reply = "I'm sorry, I couldn't generate a response."
    new_assistant_message = models.Message(
        thread_id=message.thread_id,
        role="assistant",
        content=assistant_reply
    )
    return new_assistant_message



@app.post("/api/messages", response_model=List[MessageResponse], status_code=status.HTTP_201_CREATED)
def send_message(message: MessageCreate, db: Annotated[Session, Depends(get_db)]):
    # Check if the thread exists
    thread = db.execute(
        select(models.Thread).where(models.Thread.id == message.thread_id)
    ).first()
    if not thread:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Thread not found"})

    new_message = models.Message(
        thread_id=message.thread_id,
        role=message.role,
        content=message.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    new_assistant_message = assistant_respond(new_message)

    db.add(new_assistant_message)
    db.commit()
    db.refresh(new_assistant_message)

    return [new_message, new_assistant_message]

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

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
from typing import Annotated
from database import get_db, Base, engine
from schemas import ThreadResponse, ThreadCreate
import models
from sqlalchemy.orm import Session


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
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    return new_thread




if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

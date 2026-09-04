from dotenv import load_dotenv
import os
import json
import uuid
from pathlib import Path
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from agent import get_agent
from rag import add_doc_to_rag
from tools import set_curr_thread_id
from pydantic import BaseModel
from fastapi import status
from typing import Annotated, List
from database import get_db, Base, engine
from schemas import MessageResponse, MessageCreate, ThreadResponse, ThreadCreate, RAGFileResponse
import models
from sqlalchemy.orm import Session
from sqlalchemy import select
from agent import get_agent
from rag import delete_chroma_vector_storage


load_dotenv()
Base.metadata.create_all(bind=engine)
app = FastAPI()
templates = Jinja2Templates(directory="templates/")
app.mount("/static", StaticFiles(directory="static"), name="static")
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
    new_assistant_message, tool_invocations = assistant_respond(message)
    new_assistant_message.tool_invocations = tool_invocations
    new_thread.messages.append(new_assistant_message)
    
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    # update thread's updated_at timestamp
    new_thread.updated_at = new_assistant_message.created_at
    db.commit()
    db.refresh(new_thread)

    return new_thread

@app.delete("/api/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: str, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.Thread).where(models.Thread.id == thread_id)
    )
    thread = result.scalars().first()
    if not thread:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Thread not found"})

    # delete chroma_vector_storage part which relates to the thread_id
    delete_chroma_vector_storage(thread_id)

    # delete the files itself.
    # files are located in data/rag_files
    # in db data/history.db there is table rag_files which has file_name and thread_id
    rag_files_directory = Path("data/rag_files").resolve()
    for rag_file in thread.rag_files:
        file_path = (rag_files_directory / rag_file.file_name).resolve()
        if rag_files_directory in file_path.parents:
            file_path.unlink()  # NOTE probably missing_ok not needed. WAS: (missing_ok=True)
    
    db.delete(thread)
    db.commit()

@app.post("/api/files/{thread_id}", response_model=RAGFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    thread_id: str,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
):
    thread = db.execute(
        select(models.Thread).where(models.Thread.id == thread_id)
    ).scalars().first()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    supported_extensions = {".pdf", ".docx", ".txt", ".md", ".py", ".csv", ".json"}
    if not original_name or extension not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported types: PDF, DOCX, TXT, MD, PY, CSV, JSON.",
        )

    stored_name = f"{uuid.uuid4()}{extension}"
    file_path = Path("data/rag_files") / stored_name
    try:
        file_path.write_bytes(await file.read())
        rag_result = add_doc_to_rag(str(file_path), thread_id)
        if rag_result.startswith("Error adding document to RAG:"):
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=rag_result)

        rag_file = models.RAGFile(
            file_name=stored_name,
            thread_id=thread_id,
        )
        db.add(rag_file)
        db.commit()
        db.refresh(rag_file)

        # update thread's updated_at timestamp
        thread.updated_at = rag_file.created_at
        db.commit()

        return rag_file
    except HTTPException:
        raise
    except Exception as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
    finally:
        await file.close()

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
    previous_message_count = len(agent.get_state(cfg).values.get("messages", []))
    response = agent.invoke(
        {'messages': [HumanMessage(message.content)]},
        config=cfg,
    )
    current_messages = response["messages"][previous_message_count:]
    tool_messages = {
        item.tool_call_id: item
        for item in current_messages
        if isinstance(item, ToolMessage)
    }
    tool_invocations = []
    for item in current_messages:
        if not isinstance(item, AIMessage):
            continue
        for tool_call in item.tool_calls:
            tool_message = tool_messages.get(tool_call["id"])
            if tool_message:
                result = tool_message.content
                if not isinstance(result, str):
                    result = json.dumps(result)
                tool_invocations.append(models.ToolInvocation(
                    name=tool_call["name"],
                    arguments=tool_call.get("args", {}),
                    result=result,
                ))
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
    return new_assistant_message, tool_invocations

@app.post("/api/messages", response_model=List[MessageResponse], status_code=status.HTTP_201_CREATED)
def send_message(message: MessageCreate, db: Annotated[Session, Depends(get_db)]):
    # Check if the thread exists
    thread = db.execute(
        select(models.Thread).where(models.Thread.id == message.thread_id)
    ).scalars().first()
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

    new_assistant_message, tool_invocations = assistant_respond(new_message)
    new_assistant_message.tool_invocations = tool_invocations

    db.add(new_assistant_message)
    db.commit()
    db.refresh(new_assistant_message)

    # update thread's updated_at timestamp
    thread.updated_at = new_assistant_message.created_at
    db.commit()

    return [new_message, new_assistant_message]

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

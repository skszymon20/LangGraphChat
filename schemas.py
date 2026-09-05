from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Any, List


class MessageBase(BaseModel):
    content: str = Field(min_length=1, max_length=2048, description="The content of the message.")
    thread_id: str = Field(min_length=1, max_length=36, description="The ID of the thread this message belongs to.")

class ToolInvocationResponse(BaseModel):
    id: int
    name: str
    arguments: dict[str, Any]
    result: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(MessageBase):
    id: int
    role: str = Field(min_length=1, max_length=9, description="The role of the message sender. Either 'user' or 'assistant'.")
    created_at: datetime
    tool_invocations: list[ToolInvocationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True) # Required in Pydantic v2

class MessageCreate(MessageBase):
    pass

class ThreadBase(BaseModel):
    pass

class ThreadResponse(ThreadBase):
    id: str
    title: str = Field(min_length=1, max_length=53, description="The title of the thread.")
    updated_at: datetime
    created_at: datetime
    messages: List[MessageResponse] = [] # Include the list of messages here

    model_config = ConfigDict(from_attributes=True) # Required in Pydantic v2

class ThreadCreate(ThreadBase):
    first_message: str = Field(min_length=1, max_length=2048, description="The first message, used to generate a title when no title is provided.")
    title: str | None = Field(default=None, min_length=1, max_length=53, description="The title of the thread. If not provided, it is generated from the first message.")

class RAGFileResponse(BaseModel):
    id: int
    file_name: str
    thread_id: str
    created_at: datetime
    file_path: str

    model_config = ConfigDict(from_attributes=True)

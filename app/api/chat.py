from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from app.database import get_db
from app.models.conversation import Conversation
from app.agent.graph import build_graph
import json

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


def serialize_messages(messages: list) -> str:
    """Convert LangChain message objects → JSON string for DB storage."""
    serialized = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serialized.append({"role": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serialized.append({"role": "ai", "content": m.content})
    return json.dumps(serialized)


def deserialize_messages(raw: str) -> list:
    """Convert JSON string from DB → LangChain message objects."""
    messages = []
    for m in json.loads(raw):
        if m["role"] == "human":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "ai":
            messages.append(AIMessage(content=m["content"]))
    return messages


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    # 1. Load or create conversation record
    conversation = db.query(Conversation).filter(
        Conversation.session_id == request.session_id
    ).first()

    if not conversation:
        conversation = Conversation(
            session_id=request.session_id,
            messages="[]"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Deserialize stored history into LangChain message objects
    history = deserialize_messages(conversation.messages)

    # 3. Append the new user message
    history.append(HumanMessage(content=request.message))

    # 4. Build graph and run it with full history
    try:
        graph = build_graph(db)
        result = graph.invoke({"messages": history})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # 5. Extract the last AI message as the response
    final_messages = result["messages"]
    ai_response = next(
        (m.content for m in reversed(final_messages) if isinstance(m, AIMessage)),
        "Sorry, I couldn't generate a response."
    )

    # 6. Save updated history back to DB
    # We only persist HumanMessage and AIMessage — tool messages are internal
    clean_history = [m for m in final_messages if isinstance(m, (HumanMessage, AIMessage))]
    conversation.messages = serialize_messages(clean_history)
    db.commit()

    return ChatResponse(session_id=request.session_id, response=ai_response)
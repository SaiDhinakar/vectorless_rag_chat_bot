import os
import shutil
from fastapi import FastAPI, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.database import engine, Base, get_db
from src.models import Document, Chat, Message
from src.rag import VectorlessRAG

os.makedirs("data/uploads", exist_ok=True)
os.makedirs("src/templates", exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")
try:
    rag_client = VectorlessRAG()
except Exception as e:
    print("Warning: Failed to initialize VectorlessRAG. Setup keys?", e)
    rag_client = None

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, db: Session = Depends(get_db)):
    chats = db.query(Chat).order_by(Chat.created_at.desc()).all()
    return templates.TemplateResponse(request=request, name="index.html", context={"chats": chats})

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        if not rag_client:
            return HTMLResponse("RAG client not configured. Check PAGEINDEX_API_KEY.", status_code=500)
            
        file_location = f"data/uploads/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        doc_id = rag_client.submit_document(file_location)
        
        new_doc = Document(filename=file.filename, file_path=file_location, pageindex_doc_id=doc_id)
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        new_chat = Chat(document_id=new_doc.id)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        
        return RedirectResponse(f"/chat/{new_chat.id}", status_code=303)
    except Exception as e:
        return HTMLResponse(f"Error: {str(e)}", status_code=500)

@app.get("/chat/{chat_id}", response_class=HTMLResponse)
async def get_chat(request: Request, chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return templates.TemplateResponse(request=request, name="chat.html", context={"chat": chat})

@app.get("/api/chat/{chat_id}/status")
async def check_doc_status(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return {"ready": False, "error": "Not found"}
        
    if not rag_client:
        return {"ready": False, "error": "RAG client not configured"}
        
    ready = rag_client.is_ready(chat.document.pageindex_doc_id)
    return {"ready": ready}

@app.post("/api/chat/{chat_id}/message")
async def post_message(
    chat_id: int, 
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    if not rag_client:
        raise HTTPException(status_code=500, detail="RAG client not configured")
        
    # Append user message
    user_msg = Message(chat_id=chat.id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # recent history max 6
    recent_msgs = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()[-6:]
    history_str = "\n".join([f"{m.role}: {m.content}" for m in recent_msgs])
    
    ai_response = rag_client.ask_question(
        doc_id=chat.document.pageindex_doc_id,
        query=content,
        current_chat_history_str=history_str
    )
    
    assistant_msg = Message(chat_id=chat.id, role="assistant", content=ai_response)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    return {"status": "success", "response": ai_response, "assistant_msg_id": assistant_msg.id}

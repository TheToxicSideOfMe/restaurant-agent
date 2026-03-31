from app.models import KnowledgeChunk
from embedding_service import get_embedding
from sqlalchemy.orm import Session
from sqlalchemy import text

def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    start=0
    chunks=[]
    while start<len(text):
        chunk=text[start:start+chunk_size]
        chunks.append(chunk)
        start=start+chunk_size-overlap
    return chunks


async def load_restaurant_data(db:Session):

    existing = db.execute(text("SELECT COUNT(*) FROM knowledge_chunks")).scalar()
    if existing > 0:
        return
    
    with open("app/data/restaurant_info.txt") as f:
        txt = f.read()
    chunks = split_text(txt)
    for i , chunk_text in enumerate(chunks):
        embedding = get_embedding(chunk_text)

        chunk = KnowledgeChunk(
            content = chunk_text,
            embedding = embedding
        )
        db.add(chunk)
    db.commit()


async def search_knowledge_base(question: str, db: Session) -> str:
    question_embedding = get_embedding(question)
    results = db.execute(
        text("SELECT content FROM document_chunks ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT 5"),
        { "embedding": str(question_embedding)}
    ).fetchall()

    context = "\n\n".join([row[0] for row in results])
    return context


        
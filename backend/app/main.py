from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.documents import upload_documents,get_all_documents,download_single_document
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Backend avec FastAPI et CrewAI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn


@app.get("/")
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} API - Backend is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
        "database": db_status
    }


@app.get("/api/examples")
async def get_examples():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, name, description, created_at, updated_at 
            FROM examples 
            ORDER BY id
        """)
        
        examples = cur.fetchall()
        cur.close()
        conn.close()
        
        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/examples/{example_id}")
async def get_example(example_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, name, description, created_at, updated_at 
            FROM examples 
            WHERE id = %s
        """, (example_id,))
        
        example = cur.fetchone()
        cur.close()
        conn.close()
        
        if example is None:
            raise HTTPException(status_code=404, detail="Example not found")
        
        return example
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/api/documents")
async def create_document(
    name: str = Form(...),
    doc_date: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        result = await upload_documents(name,doc_date,file)
        return result
        # conn = get_db_connection()
        # cur = conn.cursor()

        # file_bytes = await file.read()

        # cur.execute("""
        #     INSERT INTO documents (name, doc_date, file_data)
        #     VALUES (%s, %s, %s)
        #     RETURNING id, name, doc_date, created_at, updated_at
        # """, (name, doc_date, psycopg2.Binary(file_bytes)))

        # new_doc = cur.fetchone()
        # conn.commit()
        # cur.close()
        # conn.close()

        # return {
        #     "id": new_doc[0],
        #     "name": new_doc[1],
        #     "doc_date": str(new_doc[2]),
        #     "created_at": new_doc[3],
        #     "updated_at": new_doc[4]
        # }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")


@app.get("/api/documents")
async def list_documents():
    try:
        result = await get_all_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: int):
    try:
        result = await download_single_document(doc_id=doc_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {str(e)}")

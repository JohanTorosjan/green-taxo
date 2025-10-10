from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.documents import (
    upload_documents, 
    get_all_documents, 
    download_single_document,
    get_document_analysis,
    get_criterias
)
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Backend avec FastAPI, Celery et agents LLM",
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
    """
    Upload un document et déclenche automatiquement l'analyse LLM en arrière-plan
    """
    try:
        result = await upload_documents(name, doc_date, file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")


@app.get("/api/documents")
async def list_documents():
    """
    Liste tous les documents avec leur statut d'analyse
    """
    try:
        result = await get_all_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")


@app.get("/api/documents/{doc_id}/analysis")
async def get_analysis(doc_id: int):
    """
    Récupère le statut et les résultats de l'analyse d'un document
    """
    try:
        result = await get_document_analysis(doc_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: int):
    """
    Télécharge le fichier original d'un document
    """
    try:
        result = await download_single_document(doc_id=doc_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {str(e)}")
    

@app.get("/criterias/{doc_id}")
async def download_document(doc_id: int):
    """
    Recupere tout les critères d'un documents
    """
    try:
        result = await get_criterias(doc_id=doc_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recuperation des critères : {str(e)}")
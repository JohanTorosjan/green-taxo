from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Body
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.documents import (
    upload_documents, 
    get_all_documents, 
    download_single_document,
    get_document_analysis,
    get_criterias,
    toggle_used,
    upload_documents_skip,
    create_criteria,
    update_criteria,
    delete_criteria
)
from app.services.analysis import(
        upload_analysis
)

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import json 


# À ajouter en haut de main.py avec les autres imports
from pydantic import BaseModel
from app.services.auth import login_user, create_user, get_user_by_id, get_all_users
from app.dependencies import get_current_user, get_current_admin_user
from typing import Dict, Any
from fastapi import Depends



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
        print('document')

        result = await upload_documents(name, doc_date, file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")

@app.post("/api/documents/skipAi")
async def create_document(
    name: str = Form(...),
    doc_date: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload un document
    """
    try:
        result = await upload_documents_skip(name, doc_date, file)
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
async def criterias(doc_id: int):
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
    




@app.patch("/api/documents/{doc_id}")
async def update_document(doc_id: int, update_data: dict = Body(...)):
    """
    Met à jour les propriétés d'un document (actuellement: statut 'used')
    """
    used = update_data.get("used")
    
    if used is None:
        return {"success": False, "message": "Aucune modification fournie"}
    
    return await toggle_used(doc_id, used)

@app.post("/api/analysis")
async def create_analysis(
    name: str = Form(...),
    doc_date: str = Form(...),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)  # ← AJOUT ICI
):
    """
    Upload un rapport et déclenche automatiquement l'analyse LLM en arrière-plan
    Nécessite d'être authentifié
    """
    try:
        print('upload_analysis')
        print(f'User connecté: {current_user["email"]} (ID: {current_user["id"]})')
        
        # Passer le user_id à la fonction upload_analysis
        result = await upload_analysis(name, doc_date, file, current_user['id'])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")

from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
import logging
import json

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


def get_db_connection():
    from app.config import settings
    import psycopg2
    return psycopg2.connect(settings.DATABASE_URL)


@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: int):
    """
    Récupère une analyse complète par ID avec tous ses détails
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                id,
                name,
                doc_date,
                analysis_status,
                score,
                calculation_model,
                analysis_results,
                task_id,
                created_at,
                updated_at
            FROM analysis
            WHERE id = %s
        """, (analysis_id,))
        
        analysis = cur.fetchone()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        cur.close()
        conn.close()
        
        # Convertir les données
        # JSONB retourne déjà un objet Python (list/dict), pas une string JSON
        calc_model = analysis['calculation_model']
        if isinstance(calc_model, str):
            calc_model = json.loads(calc_model) if calc_model else []
        elif not isinstance(calc_model, list):
            calc_model = []
            
        analysis_res = analysis['analysis_results']
        if isinstance(analysis_res, str):
            analysis_res = json.loads(analysis_res) if analysis_res else []
        elif not isinstance(analysis_res, list):
            analysis_res = []
        
        response = {
            "id": analysis['id'],
            "name": analysis['name'],
            "doc_date": str(analysis['doc_date']),
            "analysis_status": analysis['analysis_status'],
            "score": analysis['score'],
            "task_id": analysis['task_id'],
            "created_at": analysis['created_at'].isoformat() if analysis['created_at'] else None,
            "updated_at": analysis['updated_at'].isoformat() if analysis['updated_at'] else None,
            "calculation_model": calc_model,
            "analysis_results": analysis_res
        }
        
        logger.info(f"✅ Analyse {analysis_id} récupérée avec succès")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de l'analyse {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    

@app.delete("/api/documents/{doc_id}")
async def delete_doc(doc_id: int):
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si le document existe
        cur.execute("""
            SELECT id 
            FROM documents 
            WHERE id = %s
        """, (doc_id,))
        
        document = cur.fetchone()
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document avec l'ID {doc_id} introuvable"
            )
        
        # Supprimer le document
        cur.execute("""
            DELETE FROM documents
            WHERE id = %s
        """, (doc_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Document {doc_id} supprimé avec succès"
        }
        
    except HTTPException:
        # Re-lever les HTTPException
        raise
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du document : {str(e)}"
        )
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.post("/criterias/{doc_id}")
async def create_criterias(
    doc_id: int,
    name: str = Form(...),
    description: str = Form(...),
    coeff: int = Form(...)  # Form au lieu de File
):
    """
    Upload un critère
    """
    try:
        print('OAZKEOPFKEKZFPZFPKE')
        result = await create_criteria(doc_id, name, description, coeff)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")

@app.put("/criterias/{criteria_id}")
async def update_criterias(
    criteria_id: int,
    name: str = Form(...),
    description: str = Form(...),
    coeff: int = Form(...)
):
    """
    Update un critère
    """
    try:
        result = await update_criteria(criteria_id, name, description, coeff)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour : {str(e)}")

@app.delete("/criterias/{criteria_id}")
async def delete_criterias(
    criteria_id: int
):
    """
    Supprime un critère
    """
    try:
        result = await delete_criteria(criteria_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")
    




    ########### AUTH #############
# ============= MODÈLES PYDANTIC =============

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateUserRequest(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str
    admin: bool = False


# ============= ROUTES D'AUTHENTIFICATION =============

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """
    Connexion d'un utilisateur
    Retourne un token JWT
    """
    try:
        conn = get_db_connection()
        result = login_user(conn, credentials.email, credentials.password)
        conn.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la connexion: {str(e)}")


@app.post("/api/auth/register")
async def register(user_data: CreateUserRequest, admin_user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Création d'un nouvel utilisateur (réservé aux admins)
    """
    try:
        conn = get_db_connection()
        result = create_user(
            conn,
            nom=user_data.nom,
            prenom=user_data.prenom,
            email=user_data.email,
            password=user_data.password,
            admin=user_data.admin
        )
        conn.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@app.get("/api/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté
    """
    try:
        conn = get_db_connection()
        user = get_user_by_id(conn, current_user['id'])
        conn.close()
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/users")
async def list_users(admin_user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Liste tous les utilisateurs (réservé aux admins)
    """
    try:
        conn = get_db_connection()
        users = get_all_users(conn)
        conn.close()
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/users/{user_id}")
async def get_user(user_id: int, admin_user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    Récupère un utilisateur par ID (réservé aux admins)
    """
    try:
        conn = get_db_connection()
        user = get_user_by_id(conn, user_id)
        conn.close()
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from app.config import settings
from app.tasks.document_analysis import analyze_repport_task
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import json
from typing import List, Dict, Any
logger = logging.getLogger(__name__)


def get_db_connection():
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn


async def upload_analysis(name, doc_date, file, user_id):  # ← AJOUT de user_id
    """
    Upload un rapport et déclenche l'analyse asynchrone
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        file_bytes = await file.read()

        # Insérer le document avec le statut initial 'pending'
        # Insérer le document avec le statut initial 'pending' et le user_id
        cur.execute("""
            INSERT INTO analysis (name, doc_date, file_data, analysis_status, user_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, doc_date, analysis_status, user_id, created_at, updated_at
        """, (name, doc_date, psycopg2.Binary(file_bytes), 'pending', user_id))  # ← AJOUT user_id
        

        new_analysis = cur.fetchone()
        analysis_id = new_analysis[0]
        
        conn.commit()
        
        # Déclencher la tâche d'analyse asynchrone
        logger.info(f"Déclenchement de l'analyse pour le document {analysis_id}")
        task = analyze_repport_task.delay(analysis_id)
        
        # Sauvegarder l'ID de la tâche Celery
        cur.execute("""
            UPDATE analysis 
            SET task_id = %s 
            WHERE id = %s
        """, (task.id, analysis_id))
        
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Document {analysis_id} uploadé avec succès. Task ID: {task.id}")

        return {
            "id": new_analysis[0],
            "name": new_analysis[1],
            "doc_date": str(new_analysis[2]),
            "analysis_status": new_analysis[3],
            "user_id":new_analysis[4],
            "task_id": task.id,
            "created_at": new_analysis[5],
            "updated_at": new_analysis[6],
            "message": "Document uploadé avec succès. L'analyse est en cours..."
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'upload : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")

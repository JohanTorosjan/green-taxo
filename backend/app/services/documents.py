from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from app.config import settings
from app.tasks.document_analysis import analyze_document_task
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


def get_db_connection():
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn


async def upload_documents(name, doc_date, file):
    """
    Upload un document et déclenche l'analyse asynchrone
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        file_bytes = await file.read()

        # Insérer le document avec le statut initial 'pending'
        cur.execute("""
            INSERT INTO documents (name, doc_date, file_data, analysis_status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, doc_date, analysis_status, created_at, updated_at
        """, (name, doc_date, psycopg2.Binary(file_bytes), 'pending'))

        new_doc = cur.fetchone()
        doc_id = new_doc[0]
        
        conn.commit()
        
        # Déclencher la tâche d'analyse asynchrone
        logger.info(f"Déclenchement de l'analyse pour le document {doc_id}")
        task = analyze_document_task.delay(doc_id)
        
        # Sauvegarder l'ID de la tâche Celery
        cur.execute("""
            UPDATE documents 
            SET task_id = %s 
            WHERE id = %s
        """, (task.id, doc_id))
        
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Document {doc_id} uploadé avec succès. Task ID: {task.id}")

        return {
            "id": new_doc[0],
            "name": new_doc[1],
            "doc_date": str(new_doc[2]),
            "analysis_status": new_doc[3],
            "task_id": task.id,
            "created_at": new_doc[4],
            "updated_at": new_doc[5],
            "message": "Document uploadé avec succès. L'analyse est en cours..."
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'upload : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")
        

async def get_all_documents():
    """
    Récupère tous les documents avec leur statut d'analyse
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, doc_date, analysis_status, task_id, created_at, updated_at
            FROM documents
            ORDER BY created_at DESC
        """)

        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs
    except Exception as e:
        logger.error(f"Erreur lors de la récupération : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}") 


async def get_document_analysis(doc_id: int):
    """
    Récupère le statut et les résultats de l'analyse d'un document
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, doc_date, analysis_status, task_id, 
                   analysis_results, extracted_text, created_at, updated_at
            FROM documents
            WHERE id = %s
        """, (doc_id,))

        doc = cur.fetchone()
        cur.close()
        conn.close()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")


async def download_single_document(doc_id):
    """
    Télécharge un document
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT name, file_data
            FROM documents
            WHERE id = %s
        """, (doc_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        filename, file_bytes = row
        return Response(
            content=bytes(file_bytes),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {str(e)}")
    

async def get_criterias(doc_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT *
            FROM criterias
            WHERE document_id = %s
        """, (doc_id,))

        crit = cur.fetchall()
        cur.close()
        conn.close()
        print(crit)
        if not crit:
            raise HTTPException(status_code=404, detail="No criterias found")

        return crit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

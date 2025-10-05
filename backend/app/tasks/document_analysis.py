from celery import Task
from app.celery_app import celery_app
from app.config import settings
import psycopg2
import logging
from io import BytesIO
from typing import Dict, Any
import PyPDF2
import docx

logger = logging.getLogger(__name__)


def get_db_connection():
    """Connexion à la base de données"""
    return psycopg2.connect(settings.DATABASE_URL)


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extrait le texte d'un fichier selon son type
    """
    file_lower = filename.lower()
    
    try:
        if file_lower.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        elif file_lower.endswith(('.docx', '.doc')):
            doc = docx.Document(BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        
        elif file_lower.endswith('.txt'):
            return file_bytes.decode('utf-8')
        
        else:
            return f"Type de fichier non supporté: {filename}"
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {str(e)}")
        return f"Erreur d'extraction: {str(e)}"


class DocumentAnalysisTask(Task):
    """Tâche Celery personnalisée avec retry automatique"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(base=DocumentAnalysisTask, bind=True, name='app.tasks.analyze_document')
def analyze_document_task(self, doc_id: int) -> Dict[str, Any]:
    """
    Tâche asynchrone pour analyser un document avec des agents LLM
    
    Args:
        doc_id: ID du document à analyser
        
    Returns:
        Dict avec les résultats de l'analyse
    """
    logger.info(f"Début de l'analyse du document {doc_id}")
    
    try:
        # 1. Récupérer le document depuis la DB
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, doc_date, file_data
            FROM documents
            WHERE id = %s
        """, (doc_id,))
        
        row = cur.fetchone()
        
        if not row:
            logger.error(f"Document {doc_id} non trouvé")
            return {"status": "error", "message": "Document not found"}
        
        doc_id_db, filename, doc_date, file_data = row
        
        # 2. Extraire le texte du document
        logger.info(f"Extraction du texte du document {filename}")
        print("file_data")
        print(file_data)
        text_content = extract_text_from_file(bytes(file_data), filename)
        print("text_content")
        print(text_content)
        # 3. Mettre à jour le statut du document
        cur.execute("""
            UPDATE documents 
            SET analysis_status = %s, 
                extracted_text = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ('processing', text_content[:10000], doc_id))  # Limite à 10k caractères
        
        conn.commit()
        
        # 4. Analyser le document avec les agents LLM
        logger.info(f" {doc_id}")
        
        from app.agents.llm_agents import get_analysis_agents
        
        # Créer les agents d'analyse
        agents = get_analysis_agents(provider="mistral")  # ou "anthropic", "mistral"
        
        # Préparer les métadonnées
        metadata = {
            "name": filename,
            "date": str(doc_date),
            "id": doc_id
        }
        
        # Lancer l'analyse avec les agents
        agents_result = agents.analyze_document(text_content, metadata)
        
        analysis_result = {
            "document_id": doc_id,
            "filename": filename,
            "doc_date": str(doc_date),
            "text_length": len(text_content),
            "status": "analyzed",
            "agents_results": agents_result
        }
        
        # 5. Sauvegarder les résultats de l'analyse
        cur.execute("""
            UPDATE documents 
            SET analysis_status = %s, 
                analysis_results = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ('completed', str(analysis_result), doc_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Analyse du document {doc_id} terminée avec succès")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du document {doc_id}: {str(e)}")
        
        # Mettre à jour le statut en cas d'erreur
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE documents 
                SET analysis_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, ('failed', doc_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)  # Retry après 60 secondes
from celery import Task
from app.celery_app import celery_app
from app.config import settings
import psycopg2
import logging
from io import BytesIO
from typing import Dict, Any,List
import PyPDF2
import docx

import asyncio 

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
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
        # elif file_lower.endswith(('.docx', '.doc')):
        #     doc = docx.Document(BytesIO(file_bytes))
        #     text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        #     return text
        
        # elif file_lower.endswith('.txt'):
        #     return file_bytes.decode('utf-8')
        
        # else:
        #     return f"Type de fichier non supporté: {filename}"
    
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
        text_content = extract_text_from_file(bytes(file_data), filename)
        print("text_content")
        print(text_content)

        chunks = chunk_text_by_tokens(text_content)
        print("chunks")
        print(len(chunks))

        # 3. Mettre à jour le statut du document
        cur.execute("""
            UPDATE documents 
            SET analysis_status = %s, 
                extracted_text = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ('processing', chunks[:10000], doc_id))  # Limite à 10k caractères
        
        conn.commit()
        
        logger.info(f" {doc_id}")
        
        # # Préparer les métadonnées
        metadata = {
            "name": filename,
            "date": str(doc_date),
            "id": doc_id
        }
        
        async def analyze_all_chunks():
            tasks = [run_mistral_analysis(chunk, metadata) for chunk in chunks]
            return await asyncio.gather(*tasks)

        results = asyncio.run(analyze_all_chunks())
        print("---------------AKDKKJEZJK")
        print(results)
        # result = asyncio.run(run_mistral_analysis(chunks, metadata))

        logger.info(f"Analyse Mistral terminée pour le document {doc_id}")
      
        #print(result)
        logger.info(f"Analyse Mistral terminée pour le document {doc_id}")

        try:
            # Keep connection open throughout the entire operation
            cur.execute("""
                UPDATE documents 
                SET analysis_status = %s, 
                    updated_at = CURRENT_TIMESTAMP,
                    used=true
                WHERE id = %s
            """, ('completed', doc_id))
            
            conn.commit()
            
            # Process results - connection still open
            for result_item in results:
                criteria_data = result_item.get("criterias", [])
                for criterion in criteria_data:
                    try:
                        cur.execute("""
                            INSERT INTO criterias (document_id, nom, description, coefficient, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (
                            doc_id,
                            criterion.get("name"),
                            criterion.get("description"),
                            criterion.get("coefficient")
                        ))
                        print(f"Critère sauvegardé: {criterion.get('name')}")
                        conn.commit()
                    except Exception as e:
                        print(f"Erreur lors de la sauvegarde du critère '{criterion.get('name')}': {str(e)}")
                        conn.rollback()
            
            print(f"Total de {len(criteria_data)} critères traités")
            
            return {
                "status": "success",
                "document_id": doc_id,
                "mistral_output": results
            }

        except Exception as e:
            print(f"Erreur lors de l'analyse du document {doc_id}: {str(e)}")
            conn.rollback()
            raise

        finally:
            # Close connection only once, at the very end
            cur.close()
            conn.close()



        # # Lancer l'analyse avec les agents
        # agents_result = agents.analyze_document(text_content, metadata)
        
        # analysis_result = {
        #     "document_id": doc_id,
        #     "filename": filename,
        #     "doc_date": str(doc_date),
        #     "text_length": len(text_content),
        #     "status": "analyzed",
        #     "agents_results": agents_result
        # }
        


        # print("ANALLLLLYSE TERMINEEEEEEEEEE")
        # print(result)
        # if result["status"] == "success":
        #     cur.execute("""
        #     UPDATE documents 
        #     SET analysis_status = %s, 
        #         updated_at = CURRENT_TIMESTAMP
        #     WHERE id = %s
        #     """, ('completed', doc_id))
        #     conn.commit()

        #     criteria_data = result["criteria"]
        #     print("-------------")
        #     print(criteria_data)
        #     for criterion in criteria_data.get("criteria", []):
        #         try:
        #             cur.execute("""
        #                 INSERT INTO criterias (document_id, nom, description, coefficient, created_at, updated_at)
        #                 VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        #             """, (
        #                 doc_id,
        #                 criterion.get("name"),
        #                 criterion.get("description"),
        #                 criterion.get("coefficient")
        #             ))
        #             print(f"Critère sauvegardé: {criterion.get('name')}")
        #         except Exception as e:
        #             print(f"Erreur lors de la sauvegarde du critère '{criterion.get('name')}': {str(e)}")
        #             conn.rollback()
        #             raise
        #     conn.commit()
        #     print(f"Total de {len(criteria_data.get('criteria', []))} critères sauvegardés pour le document {doc_id}")
    
        # else:
        #     print(f"Erreur lors de l'extraction: {result.get('message', 'Erreur inconnue')}")
        #     cur.execute("""
        #         UPDATE documents 
        #         SET analysis_status = %s, 
        #             updated_at = CURRENT_TIMESTAMP
        #         WHERE id = %s
        #     """, ('failed', doc_id))
        #     conn.commit()
        # cur.close()
        # conn.close()
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
            """, ('failed_2', doc_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)  # Retry après 60 secondes
    


from app.agents.llm_mistral_agent import LLMMistralAgent
import asyncio
import logging
from celery import shared_task
from typing import Dict, Any
from app.agents.llm_mistral_agent import LLMMistralAgent

logger = logging.getLogger(__name__)
async def run_mistral_analysis(text_content: str, metadata: dict) -> str:
    """
    Fonction asynchrone appelée par Celery via asyncio.run()
    """
    agent = LLMMistralAgent(model="mistral-medium-latest")


    response = await agent.extractCriteriaFromRegulation(text_content, temperature=0.2)
    print("response de ici")
    print(response)
    return response


def chunk_text_by_tokens(text: str, chunk_size: int = 8000) -> list[str]:
    """
    Divise un texte en chunks d'environ chunk_size tokens (approximatif).
    Utilise une estimation simple: 1 token ≈ 4 caractères.
    
    Args:
        text: Le texte à chunker
        chunk_size: Nombre approximatif de tokens par chunk (défaut: 8000)
        
    Returns:
        Liste de chunks de texte
    """
    # Estimation: 1 token ≈ 4 caractères
    char_size = chunk_size * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + char_size, len(text))
        
        # Si on n'est pas à la fin, chercher le dernier espace pour ne pas couper les mots
        if end < len(text):
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end + 1
    
    return chunks




async def run_mistral_repport_analysis(text_content: str, metadata: dict) -> str:
    """
    Fonction asynchrone appelée par Celery via asyncio.run()
    """
    agent = LLMMistralAgent(model="mistral-medium-latest")


    response = await agent.analyseRepport(text_content, temperature=0.2)
    print("response de ici")
    print(response)
    return response



@celery_app.task(base=DocumentAnalysisTask, bind=True, name='app.tasks.analyze_repport')
def analyze_repport_task(self, doc_id: int) -> Dict[str, Any]:
    """
    Tâche asynchrone pour analyser un rapport avec des agents LLM
    
    Args:
        doc_id: ID du rapport à analyser
        
    Returns:
        Dict avec les résultats de l'analyse
    """
    logger.info(f"Début de l'analyse du rapport {doc_id}")
    
    try:
        # 1. Récupérer le document depuis la DB
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, doc_date, file_data
            FROM analysis
            WHERE id = %s
        """, (doc_id,))
        
        row = cur.fetchone()
        
        if not row:
            logger.error(f"rapport {doc_id} non trouvé")
            return {"status": "error", "message": "rapport not found"}
        
        doc_id_db, filename, doc_date, file_data = row
        
        # 2. Extraire le texte du document
        logger.info(f"Extraction du texte du rapport {filename}")
        text_content = extract_text_from_file(bytes(file_data), filename)
        print("text_content")
        print(text_content)

        chunks = chunk_text_by_tokens(text_content)
        print("chunks")
        print(len(chunks))

        # 3. Mettre à jour le statut du document
        cur.execute("""
            UPDATE analysis 
            SET analysis_status = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ('processing', doc_id))  
        
        conn.commit()
        
        logger.info(f" {doc_id}")
        
        # # Préparer les métadonnées
        metadata = {
            "name": filename,
            "date": str(doc_date),
            "id": doc_id
        }
        calculation_model = get_calculation_model()
        print("calculation_model")

        print(calculation_model)
        async def analyze_all_chunks():
            tasks = [run_mistral_repport_analysis(chunk, metadata,) for chunk in chunks]
            return await asyncio.gather(*tasks)

        results = asyncio.run(analyze_all_chunks())
        print("---------------AKDKKJEZJK")
        print(results)
        # result = asyncio.run(run_mistral_analysis(chunks, metadata))

        logger.info(f"Analyse Mistral terminée pour le rapport {doc_id}")
      
        #print(result)
        logger.info(f"Analyse Mistral terminée pour le rapport {doc_id}")

      
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
            """, ('failed_2', doc_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)  # Retry après 60 secondes
    
def get_calculation_model() -> List[Dict[str, Any]]:
    """
    Récupère une liste de critères sélectionnés parmi tous les documents 
    et critères où 'used' est à True.
    
    Returns:
        List[Dict]: Liste des critères actifs avec leurs informations
        
    Example:
        [
            {
                "id": 1,
                "document_id": 5,
                "document_name": "Report Q1",
                "nom": "Critère 1",
                "description": "Description du critère",
                "coefficient": 2,
                "data": {"key": "value"}
            },
            ...
        ]
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Requête pour récupérer les critères actifs liés à des documents actifs
        cur.execute("""
            SELECT 
                c.id,
                c.document_id,
                d.name as document_name,
                c.nom,
                c.description,
                c.coefficient,
                c.data
            FROM criterias c
            INNER JOIN documents d ON c.document_id = d.id
            WHERE c.used = TRUE 
                AND d.used = TRUE
            ORDER BY d.id, c.id
        """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            logger.warning("Aucun critère actif trouvé")
            return []
        
        # Transformer les résultats en dictionnaire
        calculation_model = []
        for row in rows:
            criteria = {
                "id": row[0],
                "document_id": row[1],
                "document_name": row[2],
                "nom": row[3],
                "description": row[4],
                "coefficient": row[5],
                "data": row[6] if row[6] else {}
            }
            calculation_model.append(criteria)
        
        logger.info(f"Modèle de calcul chargé avec {len(calculation_model)} critères")
        return calculation_model
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du modèle de calcul: {str(e)}")
        return []
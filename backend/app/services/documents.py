from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from app.config import settings
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn


async def upload_documents(name,doc_date,file):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            file_bytes = await file.read()

            cur.execute("""
                INSERT INTO documents (name, doc_date, file_data)
                VALUES (%s, %s, %s)
                RETURNING id, name, doc_date, created_at, updated_at
            """, (name, doc_date, psycopg2.Binary(file_bytes)))

            new_doc = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return {
                "id": new_doc[0],
                "name": new_doc[1],
                "doc_date": str(new_doc[2]),
                "created_at": new_doc[3],
                "updated_at": new_doc[4]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion : {str(e)}")
        
async def get_all_documents():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, doc_date, created_at, updated_at
            FROM documents
            ORDER BY id
        """)

        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}") 

async def download_single_document(doc_id):
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
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {str(e)}")
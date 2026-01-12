# backend/app/services/dashboard.py
from datetime import date, datetime
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings


def get_db_connection():
    """Crée une connexion à la base de données"""
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn


def get_analyses_by_date(target_date: date) -> List[Dict[str, Any]]:
    """
    Récupère toutes les analyses pour une date donnée avec les informations utilisateur
    
    Args:
        target_date: La date pour laquelle récupérer les analyses
        
    Returns:
        Liste des analyses avec leurs informations associées
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Requête SQL avec JOIN pour récupérer les infos utilisateur
        # On filtre sur la date de created_at (sans l'heure)
        query = """
            SELECT 
                a.id,
                a.name,
                a.doc_date,
                a.analysis_status,
                a.company,
                a.score,
                a.created_at,
                a.updated_at,
                u.id as user_id,
                u.email as user_email,
                u.nom as user_nom,
                u.prenom as user_prenom
            FROM analysis a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE DATE(a.created_at) = %s
            ORDER BY a.created_at DESC
        """
        
        cur.execute(query, (target_date,))
        analyses = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convertir les résultats en liste de dictionnaires
        result = []
        for analysis in analyses:
            result.append({
                'id': analysis['id'],
                'name': analysis['name'],
                'doc_date': analysis['doc_date'].isoformat() if analysis['doc_date'] else None,
                'analysis_status': analysis['analysis_status'],
                'company':analysis['company'],
                'score': analysis['score'],
                'created_at': analysis['created_at'].isoformat() if analysis['created_at'] else None,
                'updated_at': analysis['updated_at'].isoformat() if analysis['updated_at'] else None,
                'user': {
                    'id': analysis['user_id'],
                    'email': analysis['user_email'],
                    'nom': analysis['user_nom'],
                    'prenom': analysis['user_prenom']
                } if analysis['user_id'] else None
            })
        
        return result
        
    except Exception as e:
        raise Exception(f"Erreur lors de la récupération des analyses: {str(e)}")


def get_analyses() -> List[Dict[str, Any]]:
    """
    Récupère toutes les analyses pour une date donnée avec les informations utilisateur
    
    Args:
        target_date: La date pour laquelle récupérer les analyses
        
    Returns:
        Liste des analyses avec leurs informations associées
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Requête SQL avec JOIN pour récupérer les infos utilisateur
        # On filtre sur la date de created_at (sans l'heure)
        query = """
            SELECT 
                a.id,
                a.name,
                a.doc_date,
                a.analysis_status,
                a.company,
                a.score,
                a.created_at,
                a.updated_at,
                u.id as user_id,
                u.email as user_email,
                u.nom as user_nom,
                u.prenom as user_prenom
            FROM analysis a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
        """
        
        cur.execute(query)
        analyses = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convertir les résultats en liste de dictionnaires
        result = []
        for analysis in analyses:
            result.append({
                'id': analysis['id'],
                'name': analysis['name'],
                'doc_date': analysis['doc_date'].isoformat() if analysis['doc_date'] else None,
                'analysis_status': analysis['analysis_status'],
                'company':analysis['company'],
                'score': analysis['score'],
                'created_at': analysis['created_at'].isoformat() if analysis['created_at'] else None,
                'updated_at': analysis['updated_at'].isoformat() if analysis['updated_at'] else None,
                'user': {
                    'id': analysis['user_id'],
                    'email': analysis['user_email'],
                    'nom': analysis['user_nom'],
                    'prenom': analysis['user_prenom']
                } if analysis['user_id'] else None
            })
        
        return result
        
    except Exception as e:
        raise Exception(f"Erreur lors de la récupération des analyses: {str(e)}")
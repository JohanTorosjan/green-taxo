import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, status
from datetime import timedelta
from app.auth_config import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from typing import Dict, Any


def authenticate_user(conn, email: str, password: str) -> Dict[str, Any]:
    """
    Authentifie un utilisateur avec email et mot de passe
    Retourne les infos de l'utilisateur si authentification réussie
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, nom, prenom, email, admin, is_active
        FROM users 
        WHERE email = %s AND password = %s
    """, (email, password))
    
    user = cur.fetchone()
    cur.close()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong Email or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    return user


def login_user(conn, email: str, password: str) -> Dict[str, Any]:
    """
    Connecte un utilisateur et retourne un token JWT
    """
    # Authentifier l'utilisateur
    user = authenticate_user(conn, email, password)
    
    # Mettre à jour la date de dernière connexion
    cur = conn.cursor()
    cur.execute("""
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP 
        WHERE id = %s
    """, (user['id'],))
    conn.commit()
    cur.close()
    
    # Créer le token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user['id']),
            "email": user['email'],
            "admin": user['admin']
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "nom": user['nom'],
            "prenom": user['prenom'],
            "email": user['email'],
            "admin": user['admin']
        }
    }


def create_user(conn, nom: str, prenom: str, email: str, password: str, admin: bool = False) -> Dict[str, Any]:
    """
    Crée un nouvel utilisateur
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérifier si l'email existe déjà
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Insérer le nouvel utilisateur
    cur.execute("""
        INSERT INTO users (nom, prenom, email, password, admin)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, nom, prenom, email, admin, created_at
    """, (nom, prenom, email, password, admin))
    
    user = cur.fetchone()
    conn.commit()
    cur.close()
    
    return {
        "id": user['id'],
        "nom": user['nom'],
        "prenom": user['prenom'],
        "email": user['email'],
        "admin": user['admin'],
        "created_at": user['created_at']
    }


def get_user_by_id(conn, user_id: int) -> Dict[str, Any]:
    """
    Récupère un utilisateur par son ID
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, nom, prenom, email, admin, is_active, created_at, last_login
        FROM users 
        WHERE id = %s
    """, (user_id,))
    
    user = cur.fetchone()
    cur.close()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return user


def get_all_users(conn) -> list:
    """
    Récupère tous les utilisateurs
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, nom, prenom, email, admin, is_active, created_at, last_login,password
        FROM users 
        ORDER BY created_at DESC
    """)
    
    users = cur.fetchall()
    cur.close()
    
    return users
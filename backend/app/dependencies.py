from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth_config import verify_token
from typing import Dict, Any

# Schéma de sécurité Bearer
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dépendance FastAPI pour récupérer l'utilisateur actuellement connecté
    Utilisation: current_user = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": int(user_id),
        "email": payload.get("email"),
        "admin": payload.get("admin", False)
    }


async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dépendance FastAPI pour vérifier que l'utilisateur connecté est admin
    Utilisation: admin_user = Depends(get_current_admin_user)
    """
    if not current_user.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user
"""
Configuration avancée pour les différents providers LLM
"""

from typing import Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMConfig:
    """Configuration pour les différents providers LLM"""
    
    OPENAI_MODELS = {
        "fast": "gpt-3.5-turbo",
        "balanced": "gpt-4",
        "powerful": "gpt-4-turbo-preview"
    }
    
    ANTHROPIC_MODELS = {
        "fast": "claude-3-haiku-20240307",
        "balanced": "claude-3-sonnet-20240229",
        "powerful": "claude-3-opus-20240229"
    }
    
    MISTRAL_MODELS = {
        "fast": "mistral-small-latest",
        "balanced": "mistral-medium-latest",
        "powerful": "mistral-large-latest"
    }
    
    @classmethod
    def get_llm_instance(cls, provider: str = "mistral", tier: str = "balanced"):
        """
        Retourne une instance du LLM configuré
        
        Args:
            provider: "openai", "anthropic", ou "mistral"
            tier: "fast", "balanced", ou "powerful"
            
        Returns:
            Instance du LLM configuré
        """
        if provider == "openai":
            return cls._get_openai_llm(tier)
        elif provider == "anthropic":
            return cls._get_anthropic_llm(tier)
        elif provider == "mistral":
            return cls._get_mistral_llm(tier)
        else:
            raise ValueError(f"Provider non supporté: {provider}")
    
    @classmethod
    def _get_openai_llm(cls, tier: str):
        """Configure et retourne un LLM OpenAI"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            logger.error("langchain_openai non installé. Installez avec: pip install langchain-openai")
            raise
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY non configurée")
        
        model = cls.OPENAI_MODELS.get(tier, cls.OPENAI_MODELS["balanced"])
        
        logger.info(f"Initialisation OpenAI avec le modèle: {model}")
        
        # Configuration minimale compatible avec OpenAI v1+
        config = {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        # Ajout de l'API key selon la méthode disponible
        try:
            # Essayer d'abord avec openai_api_key (nouvelle méthode)
            return ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, **config)
        except TypeError:
            # Fallback sur api_key (ancienne méthode)
            try:
                return ChatOpenAI(api_key=settings.OPENAI_API_KEY, **config)
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation OpenAI: {e}")
                # Dernière tentative sans spécifier explicitement l'API key
                # (elle sera lue depuis les variables d'environnement)
                import os
                os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
                return ChatOpenAI(**config)
    
    @classmethod
    def _get_anthropic_llm(cls, tier: str):
        """Configure et retourne un LLM Anthropic (Claude)"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            logger.warning("langchain_anthropic non installé, utilisation d'OpenAI par défaut")
            return cls._get_openai_llm(tier)
        
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY non configurée")
        
        model = cls.ANTHROPIC_MODELS.get(tier, cls.ANTHROPIC_MODELS["balanced"])
        
        logger.info(f"Initialisation Anthropic avec le modèle: {model}")
        
        # Configuration compatible
        config = {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        try:
            return ChatAnthropic(anthropic_api_key=settings.ANTHROPIC_API_KEY, **config)
        except TypeError:
            try:
                return ChatAnthropic(api_key=settings.ANTHROPIC_API_KEY, **config)
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation Anthropic: {e}")
                import os
                os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
                return ChatAnthropic(**config)
    
    @classmethod
    def _get_mistral_llm(cls, tier: str):
        """Configure et retourne un LLM Mistral"""
        try:
            print("mistral")
            from langchain_mistralai import ChatMistralAI
        except ImportError:
            logger.warning("langchain_mistralai non installé, utilisation d'OpenAI par défaut")
            return cls._get_openai_llm(tier)
        
        if not settings.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY non configurée")
        
        model = cls.MISTRAL_MODELS.get(tier, cls.MISTRAL_MODELS["balanced"])
        
        logger.info(f"Initialisation Mistral avec le modèle: {model}")
        
        # Configuration compatible
        config = {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        try:
            return ChatMistralAI(mistral_api_key=settings.MISTRAL_API_KEY, **config)
        except TypeError:
            try:
                return ChatMistralAI(api_key=settings.MISTRAL_API_KEY, **config)
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation Mistral: {e}")
                import os
                os.environ["MISTRAL_API_KEY"] = settings.MISTRAL_API_KEY
                return ChatMistralAI(**config)
    
    @classmethod
    def get_config_for_task(cls, task_type: str) -> Dict[str, Any]:
        """
        Retourne la configuration recommandée selon le type de tâche
        
        Args:
            task_type: "extraction", "classification", "validation", "summary"
            
        Returns:
            Dict avec provider et tier recommandés
        """
        task_configs = {
            "extraction": {
                "provider": "openai",
                "tier": "balanced",
                "description": "Extraction de données structurées"
            },
            "classification": {
                "provider": "anthropic",
                "tier": "balanced",
                "description": "Classification et catégorisation"
            },
            "validation": {
                "provider": "openai",
                "tier": "fast",
                "description": "Validation rapide des données"
            },
            "summary": {
                "provider": "anthropic",
                "tier": "powerful",
                "description": "Génération de résumés détaillés"
            },
            "analysis": {
                "provider": "anthropic",
                "tier": "powerful",
                "description": "Analyse approfondie et insights"
            }
        }
        
        return task_configs.get(task_type, {
            "provider": "openai",
            "tier": "balanced",
            "description": "Configuration par défaut"
        })

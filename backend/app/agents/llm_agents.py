"""
Agents LLM pour l'analyse de documents
Ce fichier sera étendu plus tard selon vos besoins spécifiques
"""

from crewai import Agent, Task, Crew
from app.config import settings
from app.agents.llm_config import LLMConfig
import logging
import json

logger = logging.getLogger(__name__)


class DocumentAnalysisAgents:
    """
    Classe pour gérer les agents d'analyse de documents
    """
    
    def __init__(self, llm_provider: str = "mistral", llm_tier: str = "balanced"):
        """
        Initialise les agents avec le provider LLM choisi
        
        Args:
            llm_provider: "openai", "anthropic" ou "mistral"
            llm_tier: "fast", "balanced" ou "powerful"
        """
        self.llm_provider = llm_provider
        self.llm_tier = llm_tier
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """
        Initialise le modèle LLM selon le provider choisi
        """
        try:
            print("alors?")
            print(self.llm_provider)
            return LLMConfig.get_llm_instance(
                provider=self.llm_provider,
                tier=self.llm_tier
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du LLM: {e}")
            # Fallback sur OpenAI balanced
            logger.warning("Utilisation d'OpenAI balanced comme fallback")
            return LLMConfig.get_llm_instance(provider="openai", tier="balanced")
    
    def create_extractor_agent(self):
        """
        Agent pour extraire les informations clés du document
        """
        return Agent(
            role='Extracteur de données',
            goal='Extraire les informations clés et structurées du document',
            backstory="""Vous êtes un expert en extraction de données. 
            Votre mission est d'identifier et d'extraire les informations importantes 
            d'un document de manière structurée.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_classifier_agent(self):
        """
        Agent pour classifier le document selon une taxonomie
        """
        return Agent(
            role='Classificateur de documents',
            goal='Classifier le document selon une taxonomie définie',
            backstory="""Vous êtes un expert en classification de documents.
            Vous analysez le contenu et le type de document pour le catégoriser
            correctement selon la taxonomie verte (green taxonomy).""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_validator_agent(self):
        """
        Agent pour valider et vérifier la cohérence des informations extraites
        """
        return Agent(
            role='Validateur de données',
            goal='Vérifier la cohérence et la qualité des informations extraites',
            backstory="""Vous êtes un expert en validation de données.
            Votre rôle est de vérifier que les informations extraites sont 
            cohérentes, complètes et de bonne qualité.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_document(self, text_content: str, document_metadata: dict) -> dict:
        """
        Lance l'analyse complète du document avec tous les agents
        
        Args:
            text_content: Le contenu textuel du document
            document_metadata: Métadonnées du document (nom, date, etc.)
            
        Returns:
            dict: Résultats de l'analyse
        """
        logger.info(f"Début de l'analyse LLM du document: {document_metadata.get('name')}")
        
        try:
            # Créer les agents
            extractor = self.create_extractor_agent()
            classifier = self.create_classifier_agent()
            validator = self.create_validator_agent()
            
            # Créer les tâches
            extraction_task = Task(
                description=f"""Analysez le document suivant et extrayez:
                - Les dates importantes
                - Les montants et valeurs financières
                - Les entités mentionnées (entreprises, personnes, lieux)
                - Les thèmes principaux
                - Les mots-clés pertinents
                
                Métadonnées du document:
                - Nom: {document_metadata.get('name')}
                - Date: {document_metadata.get('date')}
                
                Contenu (extrait):
                {text_content[:3000]}...
                """,
                agent=extractor
            )
            
            classification_task = Task(
                description=f"""Classifiez ce document selon les critères suivants:
                - Type de document (rapport, facture, contrat, etc.)
                - Secteur d'activité
                - Pertinence pour la taxonomie verte européenne
                - Niveau de conformité environnementale
                
                Utilisez les résultats de l'extraction précédente.
                """,
                agent=classifier
            )
            
            validation_task = Task(
                description="""Validez les informations extraites et la classification:
                - Vérifiez la cohérence des données extraites
                - Identifiez les informations manquantes ou incertaines
                - Évaluez la qualité globale de l'analyse
                - Proposez des améliorations si nécessaire
                """,
                agent=validator
            )
            
            # Créer et exécuter le crew
            crew = Crew(
                agents=[extractor, classifier, validator],
                tasks=[extraction_task, classification_task, validation_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            logger.info("Analyse LLM terminée avec succès")
            
            return {
                "status": "success",
                "extraction": str(extraction_task.output) if hasattr(extraction_task, 'output') else "N/A",
                "classification": str(classification_task.output) if hasattr(classification_task, 'output') else "N/A",
                "validation": str(validation_task.output) if hasattr(validation_task, 'output') else "N/A",
                "full_result": str(result)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse LLM: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "extraction": None,
                "classification": None,
                "validation": None
            }


def get_analysis_agents(provider: str = "openai") -> DocumentAnalysisAgents:
    """
    Factory function pour créer une instance des agents d'analyse
    
    Args:
        provider: Provider LLM à utiliser
        
    Returns:
        DocumentAnalysisAgents: Instance des agents
    """
    return DocumentAnalysisAgents(llm_provider=provider)
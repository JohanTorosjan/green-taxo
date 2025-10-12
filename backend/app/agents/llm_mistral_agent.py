"""
Agent Mistral dédié aux appels directs du modèle Chat Mistral
"""

import logging
from app.config import settings
import json
import re 
logger = logging.getLogger(__name__)

class LLMMistralAgent:
    """
    Classe pour interagir directement avec le LLM Mistral via langchain_mistralai
    """

    def __init__(self, model: str = "mistral-medium-latest"):
        """
        Initialise le modèle Mistral

        Args:
            model (str): Nom du modèle Mistral à utiliser
        """
        try:
            from langchain_mistralai import ChatMistralAI
        except ImportError:
            raise ImportError("⚠️ Le package 'langchain-mistralai' n'est pas installé. Installez-le avec : pip install langchain-mistralai")

        if not settings.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY non configurée dans settings.")

        self.model = model
        self.temperature = 0.1
        self.llm = ChatMistralAI(
            mistral_api_key=settings.MISTRAL_API_KEY,
            model=self.model,
            temperature=self.temperature,
            max_tokens=2000
        )

        logger.info(f"✅ LLMMistralAgent initialisé avec le modèle: {self.model}")

    async def callChat(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Appelle le modèle Mistral en mode asynchrone avec un prompt donné

        Args:
            prompt (str): Texte d'entrée à envoyer au modèle
            temperature (float): Niveau de créativité (0 = déterministe, 1 = plus libre)

        Returns:
            str: Réponse générée par le modèle Mistral
        """
        try:
            # On met à jour la température dynamiquement
            self.llm.temperature = temperature

            # Format standard pour les appels ChatML
            messages = [
                {"role": "system", "content": "Tu es un assistant Mistral utile et précis."},
                {"role": "user", "content": prompt}
            ]

            # L'appel asynchrone natif via langchain
            response = await self.llm.ainvoke(messages)

            # Récupère le texte généré
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'appel Mistral: {str(e)}")
            raise RuntimeError(f"Erreur Mistral: {e}")
    async def extractCriteriaFromRegulation(self, regulation_chunk: str, temperature: float = 0.05) -> dict:
        """
        Extrait les critères de conformité d'un extrait de réglementation européenne
        concernant la rédaction de rapports d'entreprises.

        Args:
            regulation_chunk (str): Extrait de texte réglementaire à analyser
            temperature (float): Température pour l'extraction (bas pour plus de précision)

        Returns:
            dict: JSON avec la structure {
                "criteriasFound": bool,
                "criterias": [
                    {
                        "name": str,
                        "description": str,
                        "coefficient": int (1-5)
                    }
                ]
            }
        """
        system_prompt = """You are an expert in European regulatory compliance for corporate reporting. Your task is to extract reporting criteria from European regulatory text.

A criterion consists of:
- name: The exact or synthesized name of the requirement
- description: A clear, detailed description of what must be present in corporate reports to satisfy this criterion
- coefficient: An importance weight from 1 to 5, where 1 is minimal importance and 5 is critical importance for compliance

IMPORTANT INSTRUCTIONS:
1. Extract only explicit criteria from the provided text
2. There may be 0 to 3 criteria per text chunk - this is normal
3. Only return valid criteria that directly relate to corporate report compliance requirements
4. Return ONLY a valid JSON object, no markdown formatting, no code blocks, no additional text
5. The response must be parseable as pure JSON

Return the response in this exact JSON format:
{
    "criteriasFound": true or false,
    "criterias": [
        {
            "name": "Criterion name",
            "description": "Clear description of what must be included in reports",
            "coefficient": 1-5
        }
    ]
}"""

        user_prompt = f"""Analyze the following excerpt from European corporate reporting regulation and extract all compliance criteria.

REGULATORY TEXT:
{regulation_chunk}

Extract all reporting criteria that companies must comply with. Remember: return ONLY valid JSON, no markdown or explanations. Returning a valid json is very important"""

        try:
            self.llm.temperature = temperature

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.llm.ainvoke(messages)
            print('-------- RESPONSE -------')
            print(response)
            response_text = response.content if hasattr(response, "content") else str(response)

            # Nettoie la réponse (supprime markdown code blocks si présents)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            response_text = re.sub(r'\s+', ' ', response_text).strip()
            response_text = response_text.replace('\\n', '\\n').replace('\\t', '\\t')
            response_text = response_text.strip().removeprefix("```json\n").removesuffix("\n```")
            response_text = response_text.replace('\\n', '\n')
            response_text = response_text.replace('\\t', '\t')


            # Parse le JSON
            
            result = json.loads(response_text)

            # Validation de la structure
            if "criteriasFound" not in result or "criterias" not in result:
                raise ValueError("Invalid response structure")

            logger.info(f"✅ Extraction réussie: {len(result['criterias'])} critère(s) trouvé(s)")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur de parsing JSON: {str(e)}")
            logger.error(f"Réponse reçue: {response_text}")
            return {
                "criteriasFound": False,
                "criterias": []
            }
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction de critères: {str(e)}")
            raise RuntimeError(f"Erreur d'extraction: {e}")
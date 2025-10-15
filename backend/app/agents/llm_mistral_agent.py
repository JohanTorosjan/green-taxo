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
2. There may be 0 to 1 criteria per text chunk - this is normal
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
        



    async def analyseRepport(self, report_chunk: str, calculation_model: list, temperature: float = 0.05) -> dict:
        """
        Analyse un chunk de rapport et vérifie sa conformité par rapport aux critères du modèle de calcul.
        
        Args:
            report_chunk (str): Extrait de texte du rapport à analyser
            calculation_model (list): Liste des critères à vérifier. Chaque critère contient:
                - nom: str (nom du critère)
                - description: str (description détaillée du critère)
            temperature (float): Température pour l'analyse (bas pour plus de précision)
        
        Returns:
            dict: JSON avec la structure {
                "analysisResults": [
                    {
                        "name": str,
                        "present": bool,
                        "justification": str or None
                    }
                ]
            }
        """
        
        # Construire la liste des critères pour le prompt
        criteria_list = "\n".join([
            f"- Criterion {i+1}: NAME: {criterion['nom']}\n  DESCRIPTION: {criterion['description']}"
            for i, criterion in enumerate(calculation_model)
        ])
        
        system_prompt = """You are an expert compliance auditor specializing in regulatory report analysis. Your task is to verify whether a report chunk satisfies specific compliance criteria.

ANALYSIS RULES:
1. For each criterion, determine if the report chunk explicitly satisfies it
2. A criterion is considered PRESENT only if there is CLEAR, EXPLICIT mention in the text
3. Ambiguous, vague, or indirect references should be considered ABSENT
4. Do NOT hallucinate or infer beyond what is explicitly stated
5. Extract exact text quotations as justification (max 3 sentences)
6. Use double quotes (") for quotations to ensure JSON compatibility
7. If a criterion is not satisfied, return null for justification

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks, no additional text. The response must be directly parseable as JSON."""

        user_prompt = f"""Analyze the following report excerpt and verify compliance with the specified criteria.

CRITERIA TO VERIFY:
{criteria_list}

REPORT EXCERPT:
{report_chunk}

For each criterion, determine:
1. If the report EXPLICITLY mentions or satisfies it (present: true/false)
2. If present=true: provide an exact quote from the text (max 3 sentences) that justifies the presence
3. If present=false: set justification to null

Return the response in this exact JSON format:
{{
    "analysisResults": [
        {{
            "name": "Criterion name",
            "present": true or false,
            "justification": "Exact quote from the report or null"
        }}
    ]
}}

CRITICAL: Return ONLY valid JSON. Do not add markdown, code blocks, or any explanations."""

        try:
            self.llm.temperature = temperature
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # Clean response (remove markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Remove unnecessary escaping and whitespace
            response_text = response_text.replace('\\n', '\n').replace('\\t', '\t')
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate structure
            if "analysisResults" not in result:
                raise ValueError("Invalid response structure: missing 'analysisResults'")
            
            if not isinstance(result["analysisResults"], list):
                raise ValueError("Invalid response structure: 'analysisResults' must be a list")
            
            # Validate each result item
            for item in result["analysisResults"]:
                if "name" not in item or "present" not in item or "justification" not in item:
                    raise ValueError("Invalid result item: missing 'name', 'present', or 'justification'")
                
                if not isinstance(item["present"], bool):
                    raise ValueError(f"Invalid 'present' value for {item['name']}: must be boolean")
            
            logger.info(f"✅ Analysis successful: {len(result['analysisResults'])} criteria checked")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {str(e)}")
            logger.error(f"Response received: {response_text}")
            return {
                "analysisResults": []
            }
        except Exception as e:
            logger.error(f"❌ Error during report analysis: {str(e)}")
            raise RuntimeError(f"Analysis error: {e}")
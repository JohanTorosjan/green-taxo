"""
EU Sustainability Regulation Criteria Extraction Agents
Extracts structured criteria from European sustainability reporting regulations
"""

from crewai import Agent, Task, Crew
from app.config import settings
from app.agents.llm_config import LLMConfig
import logging
import json

logger = logging.getLogger(__name__)


class EUSustainabilityCriteriaExtractor:
    """
    Specialized agents for extracting criteria from EU sustainability regulations
    (CSRD, ESRS, EU Taxonomy, etc.)
    """
    
    def __init__(self, llm_provider: str = "mistral", llm_tier: str = "balanced"):
        """
        Initialize agents with chosen LLM provider
        
        Args:
            llm_provider: "openai", "anthropic" or "mistral"
            llm_tier: "fast", "balanced" or "powerful"
        """
        self.llm_provider = llm_provider
        self.llm_tier = llm_tier
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM model based on chosen provider"""
        try:
            return LLMConfig.get_llm_instance(
                provider=self.llm_provider,
                tier=self.llm_tier
            )
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            logger.warning("Falling back to OpenAI balanced")
            return LLMConfig.get_llm_instance(provider="openai", tier="balanced")
    
    def create_regulation_analyzer_agent(self):
        """
        Agent specialized in understanding EU sustainability regulations structure
        """
        return Agent(
            role='EU Sustainability Regulation Analyst',
            goal='Analyze and understand the structure and requirements of EU sustainability reporting regulations',
            backstory="""You are an expert in European sustainability regulations including CSRD 
            (Corporate Sustainability Reporting Directive), ESRS (European Sustainability Reporting Standards), 
            and the EU Taxonomy. You have deep knowledge of how these regulations structure their requirements, 
            disclosure topics, and assessment criteria. You understand the hierarchy of standards, topics, 
            sub-topics, and specific datapoints. Your expertise allows you to identify mandatory vs voluntary 
            disclosures, materiality requirements, and sector-specific provisions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_criteria_extractor_agent(self):
        """
        Agent specialized in extracting individual criteria from regulatory text
        """
        return Agent(
            role='Sustainability Criteria Extraction Specialist',
            goal='Extract the 15-20 most important and actionable criteria from regulatory documents',
            backstory="""You are a meticulous expert in identifying the most critical requirements 
            from complex regulatory documents. You excel at:
            - Prioritizing the most material and impactful disclosure requirements
            - Identifying specific quantitative metrics and KPIs (Key Performance Indicators)
            - Extracting essential qualitative narrative requirements
            - Recognizing mandatory requirements and high-priority voluntary disclosures
            - Focusing on criteria that are measurable, verifiable, and actionable
            
            You understand that quality matters more than quantity - you extract 15-20 carefully 
            selected criteria that represent the core requirements of the regulation, ensuring 
            nothing critical is missed while avoiding excessive granularity.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_criteria_scorer_agent(self):
        """
        Agent specialized in assigning importance coefficients to criteria
        """
        return Agent(
            role='Criteria Weighting and Scoring Expert',
            goal='Assign appropriate importance coefficients to sustainability criteria based on regulatory priority and materiality',
            backstory="""You are an expert in determining the relative importance of sustainability 
            criteria within the EU regulatory framework. You understand how to weight criteria based on:
            - Mandatory vs voluntary nature (mandatory = higher weight)
            - Materiality and impact significance (environmental, social, governance)
            - Stakeholder relevance (investors, regulators, civil society)
            - Compliance risk and penalties for non-disclosure
            - Alignment with EU policy priorities (Green Deal, climate neutrality, circular economy)
            - Sector-specific critical issues
            
            You assign coefficients on a scale of 1-10 where:
            - 9-10: Critical mandatory disclosures with high materiality
            - 7-8: Important mandatory or highly material voluntary disclosures
            - 5-6: Standard mandatory or material voluntary disclosures
            - 3-4: Supplementary or context-dependent disclosures
            - 1-2: Optional or low-materiality disclosures
            
            You provide clear justification for each coefficient assigned.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_json_formatter_agent(self):
        """
        Agent specialized in structuring extracted criteria into clean JSON format
        """
        return Agent(
            role='JSON Structuring and Validation Expert',
            goal='Format extracted criteria into clean, standardized JSON structure with validation',
            backstory="""You are an expert in data structuring and JSON formatting. You take raw 
            extracted criteria and transform them into perfectly structured JSON that follows this schema:
            
            {
                "regulation_source": "string (e.g., ESRS E1, EU Taxonomy Article 8)",
                "extraction_date": "ISO 8601 date",
                "criteria": [
                    {
                        "id": "unique_identifier",
                        "name": "concise criterion name",
                        "description": "detailed description of what must be reported/disclosed",
                        "coefficient": integer 1-10,
                        "coefficient_justification": "brief explanation of the assigned weight",
                        "category": "environmental|social|governance|cross-cutting",
                        "subcategory": "specific topic (e.g., climate, water, employees)",
                        "metric_type": "quantitative|qualitative|both",
                        "mandatory": boolean,
                        "materiality_dependent": boolean,
                        "data_sources": ["list of typical data sources"],
                        "verification_level": "limited|reasonable|not_specified",
                        "related_standards": ["list of related ESRS/GRI/other standards"]
                    }
                ]
            }
            
            You ensure all JSON is valid, properly escaped, and complete. You catch any missing fields 
            and flag inconsistencies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def extract_criteria_from_regulation(
        self, 
        regulation_text: str, 
        document_metadata: dict
    ) -> dict:
        """
        Execute the complete criteria extraction workflow
        
        Args:
            regulation_text: Full text of the regulation document
            document_metadata: Metadata (name, regulation type, version, date)
            
        Returns:
            dict: Extracted criteria in structured JSON format
        """
        logger.info(f"Starting criteria extraction from: {document_metadata.get('name')}")
        
        try:
            # Create specialized agents
            regulation_analyzer = self.create_regulation_analyzer_agent()
            criteria_extractor = self.create_criteria_extractor_agent()
            criteria_scorer = self.create_criteria_scorer_agent()
            json_formatter = self.create_json_formatter_agent()
            
            # Task 1: Analyze regulation structure
            analysis_task = Task(
                description=f"""Analyze this EU sustainability regulation document and provide a structured overview:

**Document Information:**
- Name: {document_metadata.get('name', 'Unknown')}
- Regulation Type: {document_metadata.get('regulation_type', 'Not specified')}
- Version/Date: {document_metadata.get('version', 'Not specified')}

**Regulation Text (excerpt):**
{regulation_text[:5000]}...

**Your Analysis Must Include:**
1. **Regulation identification**: Exact name, reference number, and applicable scope
2. **Document structure**: How requirements are organized (articles, annexes, disclosure requirements, datapoints)
3. **Key themes**: Main sustainability topics covered (climate, biodiversity, social, governance, etc.)
4. **Priority requirements**: Identify the 15-20 most critical disclosure requirements
5. **Mandatory vs voluntary**: Distinction between required and optional disclosures
6. **Materiality approach**: How materiality is defined and applied
7. **Target entities**: Which companies/sectors must comply

Provide a clear, structured analysis focusing on the most material requirements.""",
                agent=regulation_analyzer,
                expected_output="A structured analysis identifying the most critical aspects and requirements of the regulation"
            )
            
            # Task 2: Extract individual criteria
            extraction_task = Task(
                description=f"""Based on the regulation analysis, extract the 15-20 MOST IMPORTANT sustainability 
criteria from the document.

**CRITICAL INSTRUCTION: Extract exactly 15-20 criteria - no more, no less.**

**Document Text:**
{regulation_text[:8000]}...

**Selection Criteria - Prioritize:**
1. **Mandatory disclosures** over voluntary ones
2. **Quantitative metrics** that are measurable and comparable
3. **High-materiality topics** (climate, emissions, social risks, governance)
4. **Core requirements** that apply to most/all companies
5. **Criteria with clear stakeholder demand** (especially investors and regulators)

**What NOT to extract:**
- Overly granular sub-metrics that can be grouped
- Optional supplementary information
- Procedural or administrative requirements
- Repetitive or overlapping criteria

**For Each of the 15-20 Criteria Provide:**
- **Name**: Clear, concise identifier (e.g., "Scope 1-2 GHG Emissions", "Employee Training Hours")
- **Description**: Detailed explanation of what must be disclosed, including measurement methodology
- **Category**: Environmental, Social, Governance, or Cross-cutting
- **Subcategory**: Specific topic (Climate Change, Water, Workforce, Business Conduct, etc.)
- **Metric type**: Quantitative, Qualitative, or Both
- **Mandatory status**: Required for all or only if material?
- **Materiality dependent**: Requires materiality assessment?
- **Typical data sources**: Where companies find this information
- **Verification requirements**: External assurance needed?
- **Related standards**: References to GRI, TCFD, etc.

**Quality over quantity**: Select the most impactful and representative criteria that capture 
the essence of the regulation.""",
                agent=criteria_extractor,
                expected_output="A focused list of exactly 15-20 high-priority criteria with complete details",
                context=[analysis_task]
            )
            
            # Task 3: Assign importance coefficients
            scoring_task = Task(
                description="""Review all extracted criteria (15-20 total) and assign an importance 
coefficient to EACH one.

**Scoring Guidelines:**

**Score 9-10 (Critical):**
- Mandatory disclosure with no materiality threshold
- High regulatory scrutiny and enforcement risk
- Direct alignment with EU Green Deal priorities
- Strong investor demand (e.g., climate metrics)
- Examples: Scope 1-2 GHG emissions, Climate transition plan

**Score 7-8 (High Importance):**
- Mandatory but may depend on materiality
- Important for high-risk sectors
- Strong stakeholder interest
- Examples: Scope 3 GHG emissions, Water in stressed areas, Worker safety

**Score 5-6 (Standard):**
- Mandatory baseline disclosures
- General applicability across sectors
- Examples: Governance structures, workforce composition

**Score 3-4 (Supplementary):**
- Context-dependent requirements
- Supporting information
- Examples: Detailed breakdowns, subsidiary data

**Score 1-2 (Low Priority):**
- Optional encouraged disclosures
- Forward-looking voluntary targets

**For Each Criterion:**
- **Coefficient**: Integer 1-10
- **Justification**: 2-3 sentences explaining the score

Ensure scoring reflects relative importance within your 15-20 selected criteria.""",
                agent=criteria_scorer,
                expected_output="All 15-20 criteria with coefficients and justifications",
                context=[extraction_task]
            )
            
            # Task 4: Format as JSON
            json_formatting_task = Task(
                description=f"""Transform all extracted and scored criteria into a clean, valid JSON structure.

**VALIDATION: Ensure exactly 15-20 criteria are included in the final JSON.**

**Required JSON Schema:**
```json
{{
    "regulation_source": "{document_metadata.get('name', 'Unknown')}",
    "regulation_type": "{document_metadata.get('regulation_type', 'EU Sustainability Regulation')}",
    "extraction_date": "{document_metadata.get('extraction_date', 'ISO 8601 date')}",
    "document_version": "{document_metadata.get('version', 'Not specified')}",
    "total_criteria_count": <must be between 15-20>,
    "criteria": [
        {{
            "id": "unique_id_using_snake_case",
            "name": "Criterion Name",
            "description": "Detailed description",
            "coefficient": <1-10>,
            "coefficient_justification": "Explanation",
            "category": "environmental|social|governance|cross-cutting",
            "subcategory": "Specific topic",
            "metric_type": "quantitative|qualitative|both",
            "mandatory": true|false,
            "materiality_dependent": true|false,
            "data_sources": ["source1", "source2"],
            "verification_level": "limited|reasonable|not_specified",
            "related_standards": ["standard1", "standard2"]
        }}
    ]
}}
```

**Validation Requirements:**
1. JSON must be valid and properly escaped
2. Exactly 15-20 criteria in the array
3. All fields populated for each criterion
4. Unique IDs in snake_case
5. Coefficients as integers 1-10
6. Booleans as true/false (not strings)
7. No empty arrays (use ["not_specified"] if needed)

**Output Format:**
Provide ONLY the valid JSON object. No markdown, no explanations.
Must be parseable by `json.loads()`.""",
                agent=json_formatter,
                expected_output="A single valid JSON object with 15-20 criteria in the specified schema",
                context=[scoring_task]
            )
            
            # Create and execute the crew
            crew = Crew(
                agents=[
                    regulation_analyzer, 
                    criteria_extractor, 
                    criteria_scorer, 
                    json_formatter
                ],
                tasks=[
                    analysis_task,
                    extraction_task, 
                    scoring_task, 
                    json_formatting_task
                ],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Try to parse the JSON result
            try:
                result_str = str(result)
                # Clean potential markdown formatting
                if "```json" in result_str:
                    result_str = result_str.split("```json")[1].split("```")[0].strip()
                elif "```" in result_str:
                    result_str = result_str.split("```")[1].split("```")[0].strip()
                
                criteria_json = safe_json_loads(result_str)
                criteria_count = len(criteria_json.get('criteria', []))
                
                # Validate criteria count
                if criteria_count < 15 or criteria_count > 20:
                    logger.warning(f"Criteria count {criteria_count} outside expected range (15-20)")
                
                logger.info(f"Successfully extracted {criteria_count} criteria")
                
                return {
                    "status": "success",
                    "criteria": criteria_json,
                    "raw_result": result_str
                }
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                return {
                    "status": "error",
                    "error": f"Failed to parse JSON: {str(e)}",
                    "raw_result": str(result)
                }
            
        except Exception as e:
            logger.error(f"Error during criteria extraction: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "criteria": None
            }


def get_criteria_extractor(provider: str = "openai", tier: str = "powerful") -> EUSustainabilityCriteriaExtractor:
    """
    Factory function to create criteria extractor instance
    
    Args:
        provider: LLM provider ("openai", "anthropic", "mistral")
        tier: "fast", "balanced", or "powerful" (recommend "powerful" for complex regulations)
        
    Returns:
        EUSustainabilityCriteriaExtractor: Configured extractor instance
    """
    return EUSustainabilityCriteriaExtractor(llm_provider=provider, llm_tier=tier)


import json
import re
import logging
from json.decoder import JSONDecodeError

logger = logging.getLogger(__name__)

def safe_json_loads(s: str):
    """Try to safely parse JSON, with cleanup for truncated or malformed responses."""
    try:
        return json.loads(s)
    except JSONDecodeError as e:
        logger.warning(f"Initial JSON decode failed: {e}")
        
        # Tentative de réparation simple :
        # 1. Supprimer tout ce qui vient après le dernier '}' valide
        s_fixed = re.split(r'}\s*$', s)[0] + '}'
        try:
            return json.loads(s_fixed)
        except JSONDecodeError:
            # Dernière tentative : ajouter un crochet fermant si liste tronquée
            if s.strip().endswith('['):
                s_fixed = s + ']'
            elif s.strip().endswith('{'):
                s_fixed = s + '}'
            try:
                return json.loads(s_fixed)
            except JSONDecodeError as e2:
                logger.error(f"Failed to fix JSON: {e2}")
                raise e2

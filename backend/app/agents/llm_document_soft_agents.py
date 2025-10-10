"""
EU Sustainability Regulation Criteria Extraction - Simplified Version
Lightweight extraction focused on essential criteria with minimal LLM calls
"""

from crewai import Agent, Task, Crew
from app.config import settings
from app.agents.llm_config import LLMConfig
import logging
import json
import re

logger = logging.getLogger(__name__)


class EUSustainabilityCriteriaSoftExtractor:
    """
    Simplified extractor for sustainability criteria - focuses on speed and efficiency
    """
    
    def __init__(self, llm_provider: str = "mistral", llm_tier: str = "balanced"):
        """
        Initialize with chosen LLM provider
        
        Args:
            llm_provider: "openai", "anthropic" or "mistral"
            llm_tier: "fast", "balanced" or "powerful"
        """
        self.llm_provider = llm_provider
        self.llm_tier = llm_tier
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM model"""
        try:
            return LLMConfig.get_llm_instance(
                provider=self.llm_provider,
                tier=self.llm_tier
            )
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            logger.warning("Falling back to OpenAI balanced")
            return LLMConfig.get_llm_instance(provider="openai", tier="balanced")
    
    def create_simple_extractor_agent(self):
        """
        Single agent for streamlined criteria extraction
        """
        return Agent(
            role='Sustainability Criteria Extractor',
            goal='Extract 10-15 key sustainability criteria with names, descriptions, and importance scores',
            backstory="""You are an expert at identifying the most important disclosure requirements 
            from sustainability regulations. You focus on extracting clear, actionable criteria quickly 
            and efficiently. You prioritize mandatory requirements and high-impact metrics.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _chunk_text(self, text: str, max_chars: int = 8000) -> list[str]:
        """
        Split long text into manageable chunks
        
        Args:
            text: Full regulation text
            max_chars: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_criteria_from_regulation(
        self, 
        regulation_text: str, 
        document_metadata: dict
    ) -> dict:
        """
        Execute simplified criteria extraction with chunking for long documents
        
        Args:
            regulation_text: Full text of the regulation document
            document_metadata: Metadata (name, regulation type, version, date)
            
        Returns:
            dict: Extracted criteria in JSON format
        """
        logger.info(f"Starting simplified extraction from: {document_metadata.get('name')}")
        
        try:
            # Check if document needs chunking
            max_chunk_size = 10000
            if len(regulation_text) > max_chunk_size:
                logger.info(f"Document is long ({len(regulation_text)} chars), processing in chunks")
                return self._extract_from_chunks(regulation_text, document_metadata, max_chunk_size)
            else:
                logger.info(f"Document size OK ({len(regulation_text)} chars), single extraction")
                return self._extract_single_pass(regulation_text, document_metadata)
            
        except Exception as e:
            logger.error(f"Error during criteria extraction: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "criteria": None
            }
    
    def _extract_single_pass(self, regulation_text: str, document_metadata: dict) -> dict:
        """
        Extract criteria from short/medium documents in one pass
        """
        extractor = self.create_simple_extractor_agent()
        
        extraction_task = Task(
            description=f"""Extract the 10-15 MOST IMPORTANT sustainability criteria from this regulation.

**Document:** {document_metadata.get('name', 'Unknown')}

**Text:**
{regulation_text}

**Instructions:**
1. Identify 10-15 key disclosure requirements (no more, no less)
2. Focus on mandatory requirements and high-materiality topics
3. Prioritize quantitative metrics over procedural requirements

**For each criterion, provide:**
- **name**: Short, clear name (e.g., "GHG Emissions Scope 1-2")
- **description**: 1-2 sentences explaining what must be disclosed
- **coefficient**: Integer 1-10 indicating importance
  * 9-10: Critical mandatory (e.g., climate emissions)
  * 7-8: Important mandatory or high-priority
  * 5-6: Standard mandatory requirements
  * 3-4: Supplementary information
  * 1-2: Optional disclosures

**Output Format (JSON only, no markdown):**
{{
    "regulation_source": "{document_metadata.get('name', 'Unknown')}",
    "extraction_date": "{document_metadata.get('extraction_date', '')}",
    "total_criteria": 10-15,
    "criteria": [
        {{
            "name": "Criterion Name",
            "description": "What must be disclosed",
            "coefficient": 8
        }}
    ]
}}

Provide ONLY valid JSON. No explanations, no markdown blocks.""",
            agent=extractor,
            expected_output="Valid JSON with 10-15 criteria containing name, description, and coefficient"
        )
        
        crew = Crew(agents=[extractor], tasks=[extraction_task], verbose=True)
        result = crew.kickoff()
        
        return self._parse_extraction_result(result, document_metadata)
    
    def _extract_from_chunks(self, regulation_text: str, document_metadata: dict, chunk_size: int) -> dict:
        """
        Extract criteria from long documents by processing chunks and merging results
        """
        chunks = self._chunk_text(regulation_text, chunk_size)
        logger.info(f"Processing {len(chunks)} chunks")
        
        all_criteria = []
        extractor = self.create_simple_extractor_agent()
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Extracting from chunk {i+1}/{len(chunks)}")
            
            extraction_task = Task(
                description=f"""Extract 3-5 key sustainability criteria from this document section.

**Document:** {document_metadata.get('name', 'Unknown')} (Part {i+1}/{len(chunks)})

**Text:**
{chunk}

**Instructions:**
1. Extract 3-5 MOST IMPORTANT criteria from THIS section
2. Focus on mandatory requirements and measurable metrics
3. Skip procedural/administrative text

**Output Format (JSON only):**
{{
    "criteria": [
        {{
            "name": "Criterion Name",
            "description": "What must be disclosed",
            "coefficient": 8
        }}
    ]
}}

Provide ONLY valid JSON.""",
                agent=extractor,
                expected_output="Valid JSON with 3-5 criteria"
            )
            
            crew = Crew(agents=[extractor], tasks=[extraction_task], verbose=False)
            
            try:
                result = crew.kickoff()
                result_str = str(result)
                
                # Clean markdown
                if "```json" in result_str:
                    result_str = result_str.split("```json")[1].split("```")[0].strip()
                elif "```" in result_str:
                    result_str = result_str.split("```")[1].split("```")[0].strip()
                print("result_strrrrrrr")
                print(result_str)
                chunk_json = safe_json_loads(result_str.strip())
                chunk_criteria = chunk_json.get('criteria', [])
                
                all_criteria.extend(chunk_criteria)
                logger.info(f"Extracted {len(chunk_criteria)} criteria from chunk {i+1}")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                continue
        
        # Merge and deduplicate criteria
        merged_criteria = self._merge_and_rank_criteria(all_criteria)
        
        final_json = {
            "regulation_source": document_metadata.get('name', 'Unknown'),
            "extraction_date": document_metadata.get('extraction_date', ''),
            "total_criteria": len(merged_criteria),
            "criteria": merged_criteria
        }
        
        logger.info(f"Final result: {len(merged_criteria)} criteria after merging")
        
        return {
            "status": "success",
            "criteria": final_json,
            "raw_result": json.dumps(final_json, indent=2)
        }
    
    def _merge_and_rank_criteria(self, all_criteria: list) -> list:
        """
        Merge criteria from multiple chunks, remove duplicates, keep top 10-15
        """
        if not all_criteria:
            return []
        
        # Deduplicate by similar names (simple approach)
        unique_criteria = {}
        for criterion in all_criteria:
            name = criterion.get('name', '').lower().strip()
            if name:
                # Keep highest coefficient if duplicate
                if name not in unique_criteria or criterion.get('coefficient', 0) > unique_criteria[name].get('coefficient', 0):
                    unique_criteria[name] = criterion
        
        # Sort by coefficient (descending) and take top 15
        sorted_criteria = sorted(
            unique_criteria.values(), 
            key=lambda x: x.get('coefficient', 0), 
            reverse=True
        )
        
        # Return top 10-15 criteria
        return sorted_criteria[:15]
    
    def _parse_extraction_result(self, result, document_metadata: dict) -> dict:
        """
        Parse and validate extraction result
        """
        try:
            result_str = str(result)
            
            # Clean markdown formatting
            if "```json" in result_str:
                result_str = result_str.split("```json")[1].split("```")[0].strip()
            elif "```" in result_str:
                result_str = result_str.split("```")[1].split("```")[0].strip()
            
            result_str = result_str.strip()
            criteria_json = result_str
            print('critera-json')
            print(criteria_json)
            criteria_count = len(criteria_json.get('criteria', []))
            
            logger.info(f"Successfully extracted {criteria_count} criteria")
            
            if not self._validate_criteria(criteria_json):
                logger.warning("Criteria validation warnings detected")
            
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
    
    def _validate_criteria(self, criteria_json: dict) -> bool:
        """
        Validate extracted criteria structure
        
        Args:
            criteria_json: Parsed JSON object
            
        Returns:
            bool: True if valid, False otherwise
        """
        is_valid = True
        
        # Check required top-level fields
        if 'criteria' not in criteria_json:
            logger.error("Missing 'criteria' field")
            return False
        
        criteria_list = criteria_json.get('criteria', [])
        
        # Check criteria count
        if len(criteria_list) < 10 or len(criteria_list) > 15:
            logger.warning(f"Criteria count {len(criteria_list)} outside expected range (10-15)")
            is_valid = False
        
        # Validate each criterion
        for idx, criterion in enumerate(criteria_list):
            if 'name' not in criterion:
                logger.warning(f"Criterion {idx} missing 'name'")
                is_valid = False
            
            if 'description' not in criterion:
                logger.warning(f"Criterion {idx} missing 'description'")
                is_valid = False
            
            if 'coefficient' not in criterion:
                logger.warning(f"Criterion {idx} missing 'coefficient'")
                is_valid = False
            else:
                coef = criterion['coefficient']
                if not isinstance(coef, int) or coef < 1 or coef > 10:
                    logger.warning(f"Criterion {idx} has invalid coefficient: {coef}")
                    is_valid = False
        
        return is_valid


def get_criteria_extractor(provider: str = "openai", tier: str = "balanced") -> EUSustainabilityCriteriaSoftExtractor:
    """
    Factory function to create soft extractor instance
    
    Args:
        provider: LLM provider ("openai", "anthropic", "mistral")
        tier: "fast", "balanced", or "powerful" (balanced recommended for speed/quality)
        
    Returns:
        EUSustainabilityCriteriaSoftExtractor: Configured extractor instance
    """
    return EUSustainabilityCriteriaSoftExtractor(llm_provider=provider, llm_tier=tier)


def safe_json_loads(s: str):
    """
    Safely parse JSON with cleanup for common issues
    """
    try:
        print("AAAAAAAAAAAAAAAAAA")
        print(s)
        print("AAAAAAAAAAAAAAAAAA")

        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.warning(f"Initial JSON decode failed: {e}")
        
        # Try to fix common issues
        s = s.strip()
        
        # Remove trailing commas
        s = re.sub(r',(\s*[}\]])', r'\1', s)
        
        # Try to find valid JSON object
        if '{' in s and '}' in s:
            # Extract from first { to last }
            start = s.find('{')
            end = s.rfind('}')
            s = s[start:end+1]
        
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # Try to close unclosed structures
            if s.count('{') > s.count('}'):
                s += '}' * (s.count('{') - s.count('}'))
            if s.count('[') > s.count(']'):
                s += ']' * (s.count('[') - s.count(']'))
            
            try:
                return json.loads(s)
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to fix JSON: {e2}")
                raise e2
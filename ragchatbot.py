from ner_model import NERManager
from wikidata_connector import WikidataConnector
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from prompt_builder import PromptBuilder
import json

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    text: str
    start: int
    end: int
    label: str
    confidence: float
    source: str


@dataclass
class ResolvedClub:
    club_name: str
    city_name: Optional[str]
    manager_name: Optional[str]
    club_content: Optional[str] = None
    manager_content: Optional[str] = None


class RAGChatbot:
    """RAG chatbot using NERManager, WikidataConnector, and PromptBuilder"""

    def __init__(self):
        logger.info("Initializing RAGChatbot with existing classes...")
        self.ner_manager = NERManager()
        self.wikidata = WikidataConnector()
        self.prompt_builder = PromptBuilder()
        logger.info("Initialization complete")

    def process_query(self, query: str, output_format: str = "simple") -> str:
        """
        Process query and return structured LLM prompt.

        Args:
            query: User question

        Returns:
            Formatted prompt string or dict depending on output_format
        """
        logger.info(f"Processing query: {query}")

        ## Extract entities using the NERManager
        ner_results = self.ner_manager.predict(query)
        entities = self._convert_entities(ner_results)

        ## Resolving a club entity
        # Sort the list in descending order by confidence score (highest first)
        entities.sort(key=lambda x: x.confidence, reverse=True)

        resolved_club = None
        for entity in entities:
            if entity.label in ("CLUBS", "CITIES"):
                club_info = self.wikidata.get_club_info(entity.text)

                if club_info:
                    resolved_club = ResolvedClub(
                        club_name=club_info["club_name"],
                        city_name=entity.text,
                        manager_name=club_info.get("manager_name"),
                        club_content=club_info.get("club_content"),
                        manager_content=club_info.get("manager_content"),
                    )
                    break  # Take first match

        ## Build structured prompt using PromptBuilder
        if resolved_club and resolved_club.manager_name:
            logger.info(f"Successfully resolved club: {resolved_club.club_name}")
            prompt_dict = self.prompt_builder.build_manager_prompt(
                user_query=query,
                club_name=resolved_club.club_name,
                city_name=resolved_club.city_name,
                manager_name=resolved_club.manager_name,
                manager_info=resolved_club.manager_content,
            )
        else:
            error_reason = "No matching Bundesliga club found or manager information unavailable"
            if entities:
                error_reason += (
                    f" for detected entities: {', '.join([e.text for e in entities[:3]])}"
                )
            logger.warning(error_reason)
            prompt_dict = self.prompt_builder.build_error_prompt(query, error_reason)

        return prompt_dict

    def _convert_entities(self, ner_results) -> List[ExtractedEntity]:
        entities = []

        for text, start, end, label, score in ner_results.get("gazetteer", []):
            entities.append(ExtractedEntity(text, start, end, label, score / 100, "gazetteer"))

        # for text, start, end, label in ner_results.get("spacy", []):
        #     entities.append(ExtractedEntity(text, start, end, label, 0.9, "spacy"))

        return entities


# Example usage
if __name__ == "__main__":
    chatbot = RAGChatbot()
    queries = [
        "Who is coaching Berlin?",
        # "What about munich?",
        # "Who is heidenheims manager?",
        # "Who is it for Pauli?",
    ]

    print("=== PROMPT FORMAT ===")
    for q in queries:
        print("=" * 50)
        print(f"Query: {q}")
        print("=" * 50)
        final_prompt = chatbot.process_query(q, "simple")
        print(json.dumps(final_prompt, indent=4, ensure_ascii=False))
        print("=" * 50)
        print()

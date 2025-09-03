from ner_model import NERManager
from wikidata_connector import WikidataConnector
import logging
from dataclasses import dataclass
from typing import List, Optional

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
    """RAG chatbot using NERManager and WikidataConnector"""

    def __init__(self):
        logger.info("Initializing RAGChatbot with existing classes...")
        self.ner_manager = NERManager()
        self.wikidata = WikidataConnector()
        logger.info("Initialization complete")

    def process_query(self, query: str) -> str:
        logger.info(f"Processing query: {query}")

        ## Extract entities using the NERManager
        ner_results = self.ner_manager.compare(query)
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
                        city_name=club_info.get("city_name"),
                        manager_name=club_info.get("manager_name"),
                        club_content=club_info.get("club_content"),
                        manager_content=club_info.get("manager_content"),
                    )
                    break  # Take first match

        ## Creating context string
        context_lines = [f"Original query: {query}", "Detected entities:"]
        for e in entities:
            context_lines.append(f"- {e.text} ({e.label})")

        if resolved_club:
            context_lines.append(f"\nResolved club: {resolved_club.club_name}")
            if resolved_club.city_name:
                context_lines.append(f"City: {resolved_club.city_name}")
            if resolved_club.manager_name:
                context_lines.append(f"Manager: {resolved_club.manager_name}")
            # if resolved_club.club_content:
            #     context_lines.append(f"Club info: {resolved_club.club_content[:400]}")
            if resolved_club.manager_content:
                context_lines.append(f"Manager info: {resolved_club.manager_content[:400]}")

        return "\n".join(context_lines)

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
        "What about munich?",
        "Who is heidenheims manager?",
        "Who is it for Pauli?",
    ]

    for q in queries:
        print("=" * 50)
        print(chatbot.process_query(q))
        print("=" * 50)

import spacy
import logging

# Required to download the pretrained English NER model before running:
# python -m spacy download en_core_web_sm

from wikidata_connector import WikidataConnector
from rapidfuzz import fuzz

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class GazetteerNER:
    """
    Simple gazetteer-based NER using fuzzy matching.
    """

    def __init__(self, entity_dict, threshold=90, max_deviation=3):
        """
        Args:
            entity_dict (dict): Dictionary of entity type -> set/list of entity strings
            threshold (int): Minimum similarity score to consider a match
            max_deviation (int): Max difference in length between entity and text span
        """
        self.entity_dict = entity_dict
        self.threshold = threshold
        self.max_dev = max_deviation

    def _best_span(self, text_lc, pat_lc):
        """
        Find the best substring of text matching pattern using fuzzy ratio.

        Args:
            text_lc (str): Lowercased input text
            pat_lc (str): Lowercased entity string

        Returns:
            tuple or None: (start_index, end_index, score) if above threshold, else None
        """
        n, m = len(text_lc), len(pat_lc)
        best = (-1, -1, -1)

        # Vary window length around entity length
        lo = max(1, m - self.max_dev)
        hi = min(n, m + self.max_dev)
        for win in range(lo, hi + 1):
            for i in range(0, n - win + 1):
                score = fuzz.ratio(pat_lc, text_lc[i : i + win])
                if score > best[2]:
                    best = (i, i + win, score)

        return best if best[2] >= self.threshold else None

    def predict(self, text):
        """
        Predict entities in text using gazetteer.

        Args:
            text (str): Input text

        Returns:
            list of tuples: (matched_text, start, end, label, score)
        """
        ents, t_lc = [], text.lower()
        for label, words in self.entity_dict.items():
            for w in words:
                m = self._best_span(t_lc, w.lower())
                if m:
                    s, e, score = m
                    ents.append((text[s:e], s, e, label, score))
        logger.info(f"Gazetteer predicted {len(ents)} entities in text")
        return ents


class GazetteerData:
    """
    Prepares gazetteer entities from Wikidata Bundesliga clubs and cities.
    """

    def __init__(self):
        self.entities = None
        self.bundesliga_clubs = None
        self._fill_b_clubs()

    def _fill_b_clubs(self):
        """
        Retrieve Bundesliga clubs and cities, preprocess, and store in entities dict.
        """
        logger.info("Fetching Bundesliga clubs and cities from Wikidata")
        client = WikidataConnector()
        self.bundesliga_clubs = client.retrieve_current_bundesliga_clubs()

        # Extract raw names
        raw_clubs = self.bundesliga_clubs["club_name"].to_list()
        raw_cities = self.bundesliga_clubs["city_name"].to_list()

        # Preprocess clubs: add full name + longest word
        clubs = []
        for club in raw_clubs:
            clubs.append(club.lower())
            longest = max(club.split(), key=len)
            clubs.append(longest.lower())

        # Preprocess cities: short (first word) + full name
        cities = []
        for c in raw_cities:
            parts = c.split()
            if parts:
                cities.append(parts[0].lower())
            cities.append(c.lower())

        # Store as sets for quick lookup
        self.entities = {
            "CLUBS": set(clubs),
            "CITIES": set(cities),
        }

        logger.info(f"Processed {len(clubs)} club entries and {len(cities)} city entries")


class NERManager:
    """
    Combines gazetteer-based and spaCy-based NER.
    """

    def __init__(self):
        # Initialize gazetteer with preprocessed entities
        logger.info("Initializing GazetteerNER and spaCy model")
        self.gazetteer = GazetteerNER(GazetteerData().entities)
        self.spacy_model = spacy.load("en_core_web_sm")

    def compare(self, text):
        """
        Compare entities detected by gazetteer and spaCy.

        Args:
            text (str): Input text

        Returns:
            dict: {"gazetteer": [...], "spacy": [...]}
        """
        gaz_ents = self.gazetteer.predict(text)
        spacy_ents = [
            (ent.text, ent.start_char, ent.end_char, ent.label_)
            for ent in self.spacy_model(text).ents
        ]
        logger.info(
            f"Detected {len(gaz_ents)} gazetteer entities and {len(spacy_ents)} spaCy entities"
        )
        return {"gazetteer": gaz_ents, "spacy": spacy_ents}


if __name__ == "__main__":
    # Initialize NER manager
    manager = NERManager()
    text = "Who is coaching munich?".lower()

    # Compare gazetteer and spaCy predictions
    results = manager.compare(text)
    for k, v in results.items():
        logger.info(f"{k} entities: {v}")

import logging
import spacy

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
        logger.info(
            f"Initialized GazetteerNER with {len(entity_dict)} entity types, "
            f"threshold={threshold}, max_deviation={max_deviation}"
        )

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

        # Try substrings with lengths around the pattern length
        lo = max(1, m - self.max_dev)
        hi = min(n, m + self.max_dev)

        for win in range(lo, hi + 1):
            for i in range(0, n - win + 1):
                score = fuzz.ratio(pat_lc, text_lc[i : i + win])
                if score > best[2]:
                    best = (i, i + win, score)

        if best[2] >= self.threshold:
            logger.debug(f"Best span found: text='{text_lc[best[0]:best[1]]}', score={best[2]}")
            return best
        return None

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

        logger.info(f"Gazetteer predicted {len(ents)} entities in text: '{text}'")
        return ents


class GazetteerData:
    """
    Prepares gazetteer entities from Wikidata Bundesliga clubs and cities.
    """

    def __init__(self):
        logger.info("Initializing GazetteerData")
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
        logger.debug(f"Retrieved {len(raw_clubs)} clubs and {len(raw_cities)} cities")

        # Preprocess clubs: full name + longest word
        clubs = []
        for club in raw_clubs:
            clubs.append(club.lower())
            longest = max(club.split(), key=len)
            clubs.append(longest.lower())

        # Preprocess cities: first word + full name
        cities = []
        for c in raw_cities:
            parts = c.split()
            if parts:
                cities.append(parts[0].lower())
            cities.append(c.lower())

        # Store results
        self.entities = {
            "CLUBS": set(clubs),
            "CITIES": set(cities),
        }
        logger.info(
            f"Processed gazetteer data: {len(clubs)} club entries, {len(cities)} city entries"
        )


class NERManager:
    """
    Combines gazetteer-based and spaCy-based NER.
    """

    def __init__(self, use_gazetteer=True, use_spacy=False, spacy_model="en_core_web_sm"):
        """
        Args:
            use_gazetteer (bool): Enable gazetteer-based NER
            use_spacy (bool): Enable spaCy NER
            spacy_model (str): Name of spaCy model to load
        """
        logger.info("Initializing NERManager")
        self.use_gazetteer = use_gazetteer
        self.use_spacy = use_spacy

        if use_gazetteer:
            logger.info("Loading GazetteerNER...")
            self.gazetteer = GazetteerNER(GazetteerData().entities)

        if use_spacy:
            logger.info(f"Loading spaCy model: {spacy_model}")
            self.spacy_nlp = spacy.load(spacy_model)

        logger.info("NERManager initialization complete")

    def predict(self, text):
        """
        Predict entities detected by gazetteer and spaCy.

        Args:
            text (str): Input text

        Returns:
            dict: {"gazetteer": [...], "spacy": [...]}
        """
        logger.info(f"Running entity prediction on text: '{text}'")
        results = {}

        # Gazetteer prediction
        if self.use_gazetteer:
            gaz_ents = self.gazetteer.predict(text)
            results["gazetteer"] = gaz_ents
            logger.info(f"Detected {len(gaz_ents)} gazetteer entities")

        # spaCy prediction
        if self.use_spacy:
            doc = self.spacy_nlp(text)
            spacy_ents = [(ent.text, ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
            results["spacy"] = spacy_ents
            logger.info(f"Detected {len(spacy_ents)} spaCy entities")

        return results


if __name__ == "__main__":
    # Example usage
    manager = NERManager(use_gazetteer=True, use_spacy=True)
    sample_text = "Who is coaching Bayern Munich in Berlin?"

    logger.info("=== Running NERManager example ===")
    results = manager.predict(sample_text)
    for k, v in results.items():
        logger.info(f"{k} entities: {v}")

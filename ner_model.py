import spacy

# Necessary in the beginning for pretrained NER model:
# python -m spacy download en_core_web_sm

from wikidata_connector import WikidataConnector
from rapidfuzz import fuzz


class GazetteerNER:
    def __init__(self, entity_dict, threshold=90, max_deviation=3):
        self.entity_dict = entity_dict
        self.threshold = threshold  # similarity cutoff
        self.max_dev = max_deviation  # how much the window can differ from entity len

    def _best_span(self, text_lc, pat_lc):
        n, m = len(text_lc), len(pat_lc)
        best = (-1, -1, -1)  # (start, end, score)
        lo = max(1, m - self.max_dev)
        hi = min(n, m + self.max_dev)
        for win in range(lo, hi + 1):
            for i in range(0, n - win + 1):
                score = fuzz.ratio(pat_lc, text_lc[i : i + win])
                if score > best[2]:
                    best = (i, i + win, score)
        return best if best[2] >= self.threshold else None

    def predict(self, text):
        ents, t_lc = [], text.lower()
        for label, words in self.entity_dict.items():
            for w in words:
                m = self._best_span(t_lc, w.lower())
                if m:
                    s, e, score = m
                    ents.append((text[s:e], s, e, label, score))
        return ents


class GazetteerData:
    def __init__(self):
        self.entities = None
        self.bundesliga_clubs = None

        self._fill_b_clubs()

    def _fill_b_clubs(self):
        client = WikidataConnector()
        self.bundesliga_clubs = client.retrieve_current_bundesliga_clubs()

        raw_clubs = self.bundesliga_clubs["club_name"].to_list()
        raw_cities = self.bundesliga_clubs["city_name"].to_list()

        # preprocess clubs: keep original + longest word
        clubs = []
        for club in raw_clubs:
            clubs.append(club.lower())
            longest = max(club.split(), key=len)
            clubs.append(longest.lower())

        # preprocess cities: short + full
        cities = []
        for c in raw_cities:
            parts = c.split()
            if parts:
                cities.append(parts[0].lower())  # short form
            cities.append(c.lower())  # full form

        self.entities = {
            "CLUBS": set(clubs),
            "CITIES": set(cities),
        }

        print()
        print(self.entities)
        print()


class NERManager:
    def __init__(self):
        self.gazetteer = GazetteerNER(GazetteerData().entities)
        self.spacy_model = spacy.load("en_core_web_sm")

    def compare(self, text):
        gaz_ents = self.gazetteer.predict(text)
        spacy_ents = [
            (ent.text, ent.start_char, ent.end_char, ent.label_)
            for ent in self.spacy_model(text).ents
        ]
        return {"gazetteer": gaz_ents, "spacy": spacy_ents}


if __name__ == "__main__":
    manager = NERManager()
    text = "Who is coaching munich?".lower()
    for k, v in manager.compare(text).items():
        print(k, v)

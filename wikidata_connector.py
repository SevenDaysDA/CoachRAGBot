import logging
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class WikidataConnector:
    def __init__(self):
        self.sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        self.sparql.setReturnFormat(JSON)
        logger.info("Initialized WikidataConnector with SPARQL endpoint")

    def retrieve_current_bundesliga_clubs(self):
        """
        Retrieve all current Bundesliga clubs with their associated city information.
        """
        logger.info("Retrieving current Bundesliga clubs from Wikidata")

        query = """
        SELECT ?club ?clubLabel ?clubCity ?clubCityLabel WHERE {
        ?club wdt:P31 wd:Q476028;
                wdt:P118 wd:Q82595;
                wdt:P159 ?clubCity.
        OPTIONAL { ?club wdt:P118 wd:Q15944511. }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        """

        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            bindings = results["results"]["bindings"]
            logger.info(f"Retrieved {len(bindings)} clubs from Wikidata")
        except Exception as e:
            logger.error(f"Failed to retrieve Bundesliga clubs: {e}")
            return pd.DataFrame()

        extracted_data = []
        for binding in bindings:
            club_data = {}

            if "club" in binding:
                club_data["club_uri"] = binding["club"]["value"]
                club_data["club_id"] = binding["club"]["value"].split("/")[-1]

            if "clubLabel" in binding:
                club_data["club_name"] = binding["clubLabel"]["value"]

            if "clubCity" in binding:
                club_data["city_uri"] = binding["clubCity"]["value"]
                club_data["city_id"] = binding["clubCity"]["value"].split("/")[-1]

            if "clubCityLabel" in binding:
                club_data["city_name"] = binding["clubCityLabel"]["value"]

            extracted_data.append(club_data)

        df = pd.DataFrame(extracted_data)
        return df

    def search_bundesliga_club(self, search_term, limit=1):
        """
        Search for Bundesliga clubs by name/alias safely
        """

        logger.info(f"Searching for club: '{search_term})")

        query = f"""
        SELECT ?club ?clubLabel ?clubCity ?manager ?managerLabel WHERE {{
          ?club wdt:P31 wd:Q476028;
                wdt:P118 wd:Q82595.
          ?club (rdfs:label|skos:altLabel) ?alias.
          FILTER(LANG(?alias) = "en").
          FILTER(CONTAINS(LCASE(?alias), "{search_term.lower()}")).
          ?club wdt:P286 ?manager.
          OPTIONAL {{ ?club wdt:P31 ?clubCity. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {min(int(limit), 10)}
        """

        try:
            self.sparql.setQuery(query)
            return self.sparql.query().convert()
        except Exception as e:
            logger.error(f"Error executing search query for '{search_term}': {e}")
            return {"results": {"bindings": []}}

    def get_wikipedia_content_from_wikidata(self, qid):
        """
        Get Wikipedia content for a Wikidata entity using the Wikipedia API
        """
        logger.info(f"Fetching Wikipedia content for QID: {qid}")
        try:
            wikidata_url = "https://www.wikidata.org/w/api.php"
            params = {"action": "wbgetentities", "ids": qid, "format": "json", "props": "sitelinks"}

            response = requests.get(
                wikidata_url, params=params, headers={"User-Agent": "Python script"}
            )
            response.raise_for_status()
            data = response.json()

            if "entities" in data and qid in data["entities"]:
                entity = data["entities"][qid]
                if "sitelinks" in entity and "enwiki" in entity["sitelinks"]:
                    page_title = entity["sitelinks"]["enwiki"]["title"]

                    wiki_url = "https://en.wikipedia.org/w/api.php"
                    wiki_params = {
                        "action": "query",
                        "format": "json",
                        "titles": page_title,
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "exsectionformat": "plain",
                    }

                    wiki_response = requests.get(
                        wiki_url, params=wiki_params, headers={"User-Agent": "Python script"}
                    )
                    wiki_response.raise_for_status()
                    wiki_data = wiki_response.json()

                    pages = wiki_data["query"]["pages"]
                    for page_id in pages:
                        if "extract" in pages[page_id]:
                            logger.info(f"Successfully retrieved Wikipedia content for {qid}")
                            return pages[page_id]["extract"]

            logger.warning(f"No Wikipedia content found for {qid}")
            return None

        except Exception as e:
            logger.error(f"Error getting Wikipedia content for {qid}: {e}")
            return None

    def get_club_info(self, search_term, include_wikipedia=True):
        """
        Get club and manager info safely with error handling
        """
        try:
            results = self.search_bundesliga_club(search_term)

            if not results["results"]["bindings"]:
                logger.warning(f"No Bundesliga club found matching '{search_term}'")
                return None

            binding = results["results"]["bindings"][0]
            club_name = binding.get("clubLabel", {}).get("value", "Unknown Club")
            manager_name = binding.get("managerLabel", {}).get("value", "Unknown Manager")

            logger.info(f"Found club '{club_name}' with manager '{manager_name}'")

            club_info = {
                "club_name": club_name,
                "manager_name": manager_name,
                "club_wikipedia_url": None,
                "club_content": None,
                "manager_wikipedia_url": None,
                "manager_content": None,
            }

            if include_wikipedia:
                club_url = binding.get("club", {}).get("value")
                manager_url = binding.get("manager", {}).get("value")

                if club_url:
                    club_qid = club_url.rstrip("/").split("/")[-1]
                    club_content = self.get_wikipedia_content_from_wikidata(club_qid)
                    club_info["club_content"] = club_content
                    if club_content:
                        club_info["club_wikipedia_url"] = (
                            f"https://en.wikipedia.org/wiki/{club_name.replace(' ', '_')}"
                        )

                if manager_url:
                    manager_qid = manager_url.rstrip("/").split("/")[-1]
                    manager_content = self.get_wikipedia_content_from_wikidata(manager_qid)
                    club_info["manager_content"] = manager_content
                    if manager_content:
                        club_info["manager_wikipedia_url"] = (
                            f"https://en.wikipedia.org/wiki/{manager_name.replace(' ', '_')}"
                        )

            return club_info

        except ValueError as e:
            logger.error(f"Input validation error: {e}")
            return None
        except KeyError as e:
            logger.error(f"Unexpected response format: {e}")
            return None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None


# Usage example
if __name__ == "__main__":
    client = WikidataConnector()

    df = client.retrieve_current_bundesliga_clubs()
    logger.info(f"Retrieved Bundesliga clubs DataFrame with {len(df)} rows")

    search_term = "leverkusen"
    club_info = client.get_club_info(search_term, include_wikipedia=True)

    if club_info:
        logger.info(f"Club: {club_info['club_name']}")
        logger.info(f"Manager: {club_info['manager_name']}")
        if club_info["club_wikipedia_url"]:
            logger.info(f"Club Wikipedia: {club_info['club_wikipedia_url']}")
        if club_info["manager_wikipedia_url"]:
            logger.info(f"Manager Wikipedia: {club_info['manager_wikipedia_url']}")
    else:
        logger.warning("No results found or query failed")

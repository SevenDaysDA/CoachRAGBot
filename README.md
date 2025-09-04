# Bundesliga RAG Chatbot

> **Note**: This is a markdown file ready for export. Save this content as `README.md` in your project directory.

A Retrieval-Augmented Generation (RAG) system that answers questions about German Bundesliga football coaches using Named Entity Recognition (NER), Wikidata integration, and structured prompt generation for LLM APIs.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technical Architecture](#technical-architecture)
- [Expected Outputs](#expected-outputs)
- [Errors of Wikidata](#known-errors-of-wikidata)
- [Answers for Additional Questions](#answers-to-additional-questions)




## Features

- **Named Entity Recognition**: Hybrid approach using gazetteer-based matching and spaCy NLP
- **Real-time Data**: Fetches current Bundesliga club and manager information from Wikidata
- **Wikipedia Integration**: Enriches responses with biographical content from Wikipedia
- **Structured Prompts**: Generates properly formatted prompts for LLM APIs (OpenAI, Anthropic, etc.)
- **Fuzzy Matching**: Handles variations in club names and city references
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Prerequisites

Before running this project, ensure you have the following installed:

- **Python 3.8+**
- **pip** (Python package installer)
- **Internet connection** (for Wikidata and Wikipedia API calls)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bundesliga-rag-chatbot
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
(Optional if you want to use a out-of-shelf ner model)
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Configuration


### Environment Setup

No additional configuration files are needed. The system uses:
- **Wikidata SPARQL endpoint**: `https://query.wikidata.org/sparql`
- **Wikipedia API**: `https://en.wikipedia.org/w/api.php`

## Usage

### DEMO with console interface

```bash
python console_interface.py
```

### Output responses for a list of queries

```python
from rag_chatbot import RAGChatbot

# Initialize the chatbot
chatbot = RAGChatbot()

# Process a query
result = chatbot.process_query("Who is coaching Köln?")
print(result)
```

### Command Line Demo

```bash
python rag_chatbot.py
```

This will run example queries and display the structured prompts.


### Output Format

The system returns structured prompts ready for LLM APIs:

```json
{
    "system": "You are a German Bundesliga football expert assistant...",
    "user": "1. FC Köln City: Köln Current Manager: Lukas Kwasniok Manager Background: Lukas Kwasniok (born 12 June 1981) is a Polish-German professional football manager and former player who is the head coach of Bundesliga club 1. FC Köln. USER QUESTION: Who is coaching Köln?",
    "context": {
        "club_name": "1. FC Köln",
        "manager_name": "Lukas Kwasniok",
        "manager_info": "Lukas Kwasniok (born 12 June 1981) is a Polish-German professional football manager and former player who is the head coach of Bundesliga club 1. FC Köln."
    }
}
```

## Project Structure

```
├── rag_chatbot.py          # Main RAG system orchestrating all components
├── ner_model.py            # NER implementation (gazetteer + fuzzy match)
├── wikidata_connector.py   # Wikidata and Wikipedia API integration
├── prompt_builder.py       # Structured prompt generation for LLMs
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Architecture

### Core Components

1. **RAGChatbot** (`rag_chatbot.py`)
   - Main orchestrator class
   - Coordinates entity extraction, data retrieval, and prompt generation
   - Handles confidence-based entity resolution

2. **NERManager** (`ner_model.py`)
   - **GazetteerNER**: Fuzzy matching against Bundesliga club/city names
   - **GazetteerData**: Preprocesses club names with variations and aliases

3. **WikidataConnector** (`wikidata_connector.py`)
   - SPARQL queries to Wikidata for current Bundesliga information
   - Wikipedia content retrieval for biographical information
   - Comprehensive error handling and fallback mechanisms

4. **PromptBuilder** (`prompt_builder.py`)
   - Generates system/user message pairs for LLM APIs
   - Handles both successful matches and error cases
   - Maintains context separation for optimal LLM performance



### Expected Outputs

The system should successfully resolve queries about current Bundesliga managers and return structured prompts with:
- Club name and location
- Current manager name
- Biographical information from Wikipedia
- Proper system/user message formatting


### Known errors of Wikidata

Both at the time of the tests (04.09.2025)
- FC Augsburg: For Augsburg the program would not give any answers because the team is not listed as a meber of the bundesliga in wikidata. it was deprecated as bundesliga team and newer renewed.
- Bayer 04 Leverkusen: Leverkusen has currently no trainer since 01.09.25.. Wikidata has a white space for this case. We could retrieve the last active manager, but this would deceive the function of recent information.




# ANSWERS to Additional Questions

## 1. What are advantages and disadvantages of using additional information for a chatbot instead of letting the LLM answer without it?

Using additional information allows the chatbot to provide fresh and up-to-date answers. It also makes the content more controllable and helps reduce hallucinations, since the chatbot can rely on external sources instead of generating facts from memory. If false or outdated information is present, it can be corrected by updating the external data, whereas an LLM would require retraining. Another benefit is that smaller language models can be used, because the system depends more on linguistic capabilities than on stored knowledge.

However, this approach introduces extra complexity. External data sources and the infrastructure to manage them need to be maintained, which increases development effort. In addition, when knowledge graphs or third-party services are involved, queries can take longer to resolve. This can lead to higher latency compared to a model that answers directly from its internal knowledge.


## 2. What are advantages and disadvantages of querying for this data on every user question?

Querying the data on every user question ensures that the chatbot always works with the most up-to-date information. If details change while the system is running, they are reflected immediately in the response, which guarantees real-time accuracy.

On the other hand, this approach comes with clear drawbacks. Each query increases latency, which can slow down the user experience. It also makes the system dependent on external services. If a system is unavailable or the rate is limited, the chatbot will fail to provide an answer.



## 3. How would the process change if the information about coaches only were available via pdf?

The approach would depend on the structure of the data within the PDFs.

- If the data is semi-structured (e.g., tables or consistent formatting), it would be best to transform it into a knowledge graph and query it directly, similar to how Wikidata is used.
- If the data is unstructured text, a content chunking approach could be more feasible. The chunks could then be embedded and indexed in a vector database to enable semantic retrieval.

Bot processes would require a PDF loader with layout-aware extraction.

## 4. Do you see potential for agents in this process? If so, where and how?

Agents can enhance the flexibility and robustness of the retrieval pipeline. They can coordinate multi-step workflows, such as querying Wikidata with SPARQL, performing entity disambiguation, and enriching the results with Wikipedia summaries. Agents can also support error recovery by handling situations where data is incomplete or missing, for example by checking alternative labels or using language-model similarity to infer the correct information. Additionally, agents can help with data management by maintaining periodic caches of club and coach information, refreshing knowledge on a regular schedule, and monitoring for changes or inconsistencies over time.

## 5. How do these kinds of processes profit from a data model that models the specific domain knowledge?

A dedicated data model provides clear relationships (e.g., City → Club → Manager), which improves disambiguation and reduces errors.
It also enables structured multi-hop queries, making retrieval more efficient and flexible. For example:
- Historical queries: “Who coached Bayern between 2015–2020?”
- Multi-entity queries: “Which cities have multiple Bundesliga teams?”

A domain-specific model ensures consistency and supports complex reasoning. It also simplifies the extension of the system to new use cases.



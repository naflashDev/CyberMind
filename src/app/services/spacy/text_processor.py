## \file text_processor.py
## \brief Processes multilingual texts by detecting language and extracting named entities using spaCy.


import spacy
import json
import os
from langdetect import detect
from loguru import logger
from app.utils.utils import get_connection_parameters,create_config_file
from app.models.opensearh_db import store_in_opensearch,text_exists_in_opensearch,ensure_index_exists

# Load spaCy models by language (Spanish, English, and French)
models = {
    'es': spacy.load("es_core_news_sm"),
    'en': spacy.load("en_core_web_sm"),
    'fr': spacy.load("fr_core_news_sm"),
}

def detect_language(text):
    '''
    @brief Detects the language of a text.
    @param text Text in string format to analyze.
    @return ISO 639-1 code of the detected language (e.g., 'es', 'en', 'fr').
    '''
    try:
        return detect(text)
    except:
        return 'es'  # Default value if detection fails

def tag_text(text):
    '''
    @brief Tags named entities in a text by automatically detecting the language.
    @param text Text to process.
    @return A tuple with the list of found entities [(text, type)] and the detected language.
    '''
    language = detect_language(text)
    model = models.get(language, models['es'])  # Use Spanish model if language is not supported
    doc = model(text)
    return [(ent.text, ent.label_) for ent in doc.ents], language

def extract_texts(data):
    '''
    @brief Extracts relevant text strings from the input JSON data.
    @param data JSON object (dict) with keys like title, h1, h2, h3, h4, p, etc.
    @return List of text strings extracted from the JSON.
    '''
    texts = []

    # Extract title if present
    if 'title' in data and data['title']:
        texts.append(data['title'])

    # Extract lists of strings from h1, h2, h3, h4, p keys
    for key in ['h1', 'h2', 'h3', 'h4', 'p']:
        if key in data and isinstance(data[key], list):
            texts.extend([item for item in data[key] if isinstance(item, str) and item.strip() != ""])

    return texts

def process_json(input_path, output_path):
    '''
    @brief Processes an input JSON file, tagging texts by language, and saves the results to another JSON.
    @param input_path Path to the input JSON file.
    @param output_path Path where the result JSON file will be saved.
    @return List of results with text, language, tags, and relevance (number of tags).
    '''
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The input data can be either a dict or a list of dicts; normalize to a list
    records = data if isinstance(data, list) else [data]

    results: list[dict] = []

    # Default OpenSearch connection parameters (will be overridden if cfg.ini exists)
    parameters: tuple = (
        'localhost',
        9200
    )
    file_name: str = 'cfg.ini'
    file_content: list[str] = [
        '# Configuration file.\n',
        '# This file contains the parameters for connecting to the OpenSearch database server.\n',
        '# ONLY one uncommented line is allowed.\n',
        '# The valid line format is: server_ip;server_port\n',
        f'{parameters[0]};{parameters[1]}\n'
    ]

    # Get connection parameters or recreate configuration file if needed
    retorno_otros = get_connection_parameters(file_name)
    logger.info(retorno_otros[1])

    if retorno_otros[0] != 0:
        logger.info('Recreating configuration file...')
        retorno_otros = create_config_file(file_name, file_content)
        logger.info(retorno_otros[1])

        if retorno_otros[0] != 0:
            logger.error('Configuration file missing. Execution cannot continue without a configuration file.')
            return
    else:
        parameters = retorno_otros[2]  # Parameters read from the config file


    # Local set to avoid duplicate texts within the same execution
    processed_texts: set[str] = set()

    #Ensure the index exists in OpenSearch
    ensure_index_exists(parameters[0], parameters[1], "spacy_documents")

    for record in records:
        texts = extract_texts(record)
        for text in texts:
            if not text.strip():
                continue

            # Skip duplicates inside the same run
            if text in processed_texts:
                continue

            if text_exists_in_opensearch(text, parameters[0], parameters[1], "spacy_documents"):
                logger.info(f"Text already indexed, skipping: {text[:80]}...")
                continue

            processed_texts.add(text)

            tags, detected_language = tag_text(text)
            doc = {
                "text": text,
                "language": detected_language,
                "tags": tags,
                "relevance": len(tags)
            }
            results.append(doc)

    # Sort results by number of named entities (relevance) in descending order
    results.sort(key=lambda x: x["relevance"], reverse=True)

    # Save results to the output JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # Store each new document in OpenSearch
    for doc in results:
        store_in_opensearch(doc, parameters[0], parameters[1], "spacy_documents")

    return results

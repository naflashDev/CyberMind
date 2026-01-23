"""
@file opensearh_db.py
@author naflashDev
@brief OpenSearch integration for storing processed data.
@details Provides methods to connect and store extracted content in OpenSearch, using basic authentication and custom index management.
"""

from opensearchpy import OpenSearch, NotFoundError, TransportError
from loguru import logger

def store_in_opensearch(data,host,port,nom_index) -> None:
    '''
    @brief Stores the processed data in OpenSearch.

    Connects to a local OpenSearch instance and stores the extracted and filtered content (such as text and keywords) in the specified index.

    @param data The data to store in OpenSearch (dict). Typically includes the URL, text, and keywords.
    @param host The host of the OpenSearch server (str).
    @param port The port of the OpenSearch server (int).
    @param nom_index Name of the index to store the data (str).
    @return None.
    '''
    try:

        logger.info(f"Connecting to OpenSearch instance at {host}:{port}.")

        client = OpenSearch(
            hosts=[{'host': host, 'port': port}]
        )

        response = client.index(index=nom_index, body=data)

        logger.info(
            f"Document indexed successfully. Response: {response['result']}"
        )

    except Exception as e:
        logger.error(f"Error while storing data in OpenSearch: {e}")

def text_exists_in_opensearch(text: str, host: str, port: int, index_name: str = "spacy_documents") -> bool:
    '''
    @brief Check if a document with the same 'text' field already exists in OpenSearch.

    Searches the specified OpenSearch index for a document with the exact same text value.

    @param text Text to search for (str).
    @param host OpenSearch server IP or hostname (str).
    @param port OpenSearch server port (int).
    @param index_name Name of the index where documents are stored (str).
    @return True if at least one document with the same text already exists, False otherwise (bool).
    '''
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )

    # Exact search on the 'text.keyword' field (requires keyword subfield in the mapping)
    try:
        query = {
            "query": {
                "term": {
                    "text.keyword": text
                }
            },
            "size": 1
        }

        resp = client.search(index=index_name, body=query)
        hits_total = resp.get("hits", {}).get("total", {})
        # OpenSearch may return an int or a dict with 'value'
        if isinstance(hits_total, int):
            return hits_total > 0
        return hits_total.get("value", 0) > 0
    except Exception as e:
        logger.error(f"No existe el indice: {e}")
        return False

def ensure_index_exists(host: str, port: int, index_name: str = "spacy_documents") -> None:
    '''
    @brief Ensure that the given OpenSearch index exists. If it does not exist, create it.

    Checks if the specified index exists in OpenSearch and creates it with the required mapping if not present.

    @param host OpenSearch server IP or hostname (str).
    @param port OpenSearch server port (int).
    @param index_name Name of the index to check/create (str).
    @return None.
    '''
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )

    try:
        if not client.indices.exists(index=index_name):
            # Minimal mapping: text with keyword subfield so term query on text.keyword works
            body = {
                "mappings": {
                    "properties": {
                        "text": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "language": {"type": "keyword"},
                        "tags": {
                            "type": "keyword",
                            "index": False  
                        },
                        "relevance": {"type": "integer"},
                    }
                }
            }
            client.indices.create(index=index_name, body=body)
            logger.info(f"Index '{index_name}' created in OpenSearch.")
    except TransportError as e:
        logger.error(f"Error checking/creating index '{index_name}': {e}")
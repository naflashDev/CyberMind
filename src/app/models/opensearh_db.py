# @ Author: naflashDev
# @ Create Time: 2025-04-22 12:17:59
# @ Project: Cebolla
# @ Description: Main entry point for running the application in a development
# environment.
#
# This script cointeins the methots to save de information in opensearch
from opensearchpy import OpenSearch, NotFoundError, TransportError
from loguru import logger

def store_in_opensearch(data,host,port,nom_index) -> None:
    """
    Stores the processed data in OpenSearch.

    This function connects to a local OpenSearch instance and stores the
    extracted and filtered content (such as text and keywords) in an index
    called "documents". The OpenSearch instance is configured to use basic
    authentication.

    Args:
        data (dict): The data to store in OpenSearch. Typically includes the
        URL, text, and keywords.
        host (str): The host of the OpenSearch server (e.g., "localhost").
        port (int): The port of the OpenSearch server (e.g., 9200).
        nom_index(str): Name of the Index to store the data.
    """
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
    """
    Check if a document with the same 'text' field already exists in OpenSearch.

    Parameters:
        text (str): Text to search for.
        host (str): OpenSearch server IP or hostname.
        port (int): OpenSearch server port.
        index_name (str): Name of the index where documents are stored.

    Returns:
        bool: True if at least one document with the same text already exists, False otherwise.
    """
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
    """
    Ensure that the given OpenSearch index exists. If it does not exist, create it.

    Parameters:
        host (str): OpenSearch server IP or hostname.
        port (int): OpenSearch server port.
        index_name (str): Name of the index to check/create.
    """
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
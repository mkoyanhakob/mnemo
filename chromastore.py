import chromadb
import logging
import os

logger = logging.getLogger('Mnemo')

chromadb_host = os.getenv('CHROMADB_HOST')
chromadb_port = os.getenv('CHROMADB_PORT')
collection_name = os.getenv('COLLECTION_NAME')
query_results_number = os.getenv("QUERY_RESULTS_NUMBER")

class ChromaStore():
    def __init__(self):
        self.client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None, # Custom embedder is used: Sentence Transformers.
            metadata={
                'hnsw:space': 'ip' # Running the 'dot products' to have magnitudes included.
            }
        )

        logger.info('Connected to ChromaDB cluster service.')
        
    def save(self, key_id, embedding, document, metadata):
        try:
            self.collection.add(
                ids=[key_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata]
            )

            return True
        except Exception as e:
            logger.error(f'Chroma insert failed for {key_id}: {e}')
            return False
        
    def ask(self, q_embeddings=None, n_results=int(query_results_number)):
        if q_embeddings == None:
            logger.error('Can not retrieve data with no query!')
        else:
            try:
                result = self.collection.query(
                    query_embeddings=[q_embeddings],
                    n_results=n_results
                )

                return result
            except Exception as e:
                logger.error('Unable to make query!')
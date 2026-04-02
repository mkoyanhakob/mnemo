from sentence_transformers import SentenceTransformer
import logging
import os

logger = logging.getLogger('Mnemo')

sentence_transformer_model = os.getenv('SENTENCE_TRANSFORMER_MODEL')

class Embedder:
    def __init__(self):
        logger.info(f'Initializing SentenceTransformer: {str(sentence_transformer_model)}')
        try:
            self.model = SentenceTransformer(str(sentence_transformer_model))
            logger.info('Model loaded successfully on device: %s', self.model.device)
        except Exception as e:
            logger.error('Mnemo: Failed to load embedding model: %s', e)
            raise

    def embed(self, data):
        try:
            embedding = self.model.encode(data).tolist()
            
            return embedding
        except Exception as e:
            logger.error('Mnemo: Embedding generation failed: %s', e)
            return None
from etcdstore import EtcdManager
from chunker import Chunker
from embedder import Embedder
from chromastore import ChromaStore
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mnemo.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('Mnemo')

class MnemoCore():
    def __init__(self):
        self.etcd_manager = EtcdManager()
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.chroma_store = ChromaStore()

    def _pipeline(self):
        while True:
            try:
                raw_data = self.etcd_manager.event()
                if not raw_data:
                    continue

                chunking = self.chunker.process(raw_data)

                if chunking is None:
                    continue

                text = chunking.get('document')
                if not text:
                    continue

                embedding = self.embedder.embed(chunking['document'])

                stored = self.chroma_store.save(
                    chunking['id'], 
                    embedding,
                    chunking['document'], 
                    chunking['metadata']
                    )

            except Exception as e:
                logger.error(f'Pipeline stalled: {e}')

    def run(self):
        self._pipeline()

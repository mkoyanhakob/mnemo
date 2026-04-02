import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from embedder import Embedder
from viz import Visualizer
from narrator import MnemoNarrator
import logging
import os

logger = logging.getLogger("Mnemo")

api_port = os.getenv('API_PORT')
api_host = os.getenv('API_HOST')

class MnemoApi():
    def __init__(self, core_instance):
        self.core = core_instance

        self.app = FastAPI()
        self.embedder = Embedder()
        self.visualizer = Visualizer()
        self.narrator = MnemoNarrator()

        self.setup_routes()

    def setup_routes(self):
        @self.app.get("/ui")
        def ui_viz():
            viz = self.visualizer.run_viz()

            return HTMLResponse(content=viz, status_code=200)

        @self.app.get('/ask')
        def ask_mnemo(q: str = None):
            if q is None:
                logger.error("No query provided!")
            query_vector = self.embedder.embed(q)
            artifacts = self.core.chroma_store.ask(q_embeddings=query_vector)

            llm_summary = self.narrator.summarize(artifacts, q)

            return {
                "summary": llm_summary
            }
        
    def run_api(self):
        uvicorn.run(self.app, host=str(api_host), port=api_port)
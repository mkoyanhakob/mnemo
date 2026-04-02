import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from chromadb import HttpClient
import os

chromadb_host = os.getenv('CHROMADB_HOST')
chromadb_port = os.getenv('CHROMADB_PORT')
collection_name = os.getenv('COLLECTION_NAME')

class Visualizer():
    def __init__(self):
        self.client = HttpClient(host=str(chromadb_host), port=chromadb_port)

    def run_viz(self):
        self.collection = self.client.get_collection(str(collection_name))
        self.res = self.collection.get(include=['embeddings', 'documents', 'metadatas'])

        count = len(self.res['ids'])
        if count < 3:
            print(f"Need 3+ artifacts. Found: {count}")
            return

        # PCA 384D -> 3D
        pca = PCA(n_components=3).fit_transform(self.res['embeddings'])
        df = pd.DataFrame(pca, columns=['x', 'y', 'z'])
        df['text'] = self.res['documents']

        # Colorising, use 'reason' if it exists in metadata, otherwise use the unique ID
        labels = []
        for i in range(count):
            m = self.res['metadatas'][i] if self.res['metadatas'] else {}
            # If 'reason' is in the metadata, use it. Otherwise, use ID for colors.
            label = m.get('reason') or self.res['ids'][i]
            labels.append(label)
        
        df['label'] = labels

        fig = px.scatter_3d(
            df, x='x', y='y', z='z', 
            color='label', 
            hover_data=['text'],
            title=f"Mnemo Archaeology: {count} Events",
            template="plotly_dark"
        )

        return fig.to_html(full_html=True, include_plotlyjs='cdn')
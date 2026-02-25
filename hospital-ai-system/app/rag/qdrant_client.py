from qdrant_client import QdrantClient
from app.config.settings import settings

client = QdrantClient(url=settings.QDRANT_URL)

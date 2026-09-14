import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
DB_PATH = ROOT / 'chroma_db'
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')
DISCLAIMER = ('Educational drug information from the selected prescribing PDF, not medical advice. '
              'Do not start, stop, or change treatment based on this answer. Consult a qualified healthcare '
              'professional and read the full prescribing information. AI can misinterpret text, tables, or '
              'images; check the cited pages. For urgent symptoms, seek emergency care.')
NOT_FOUND = "I couldn't verify this information from the available prescribing documents."


def collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(DB_PATH))
    result = client.get_or_create_collection('drug_labels', metadata={'hnsw:space': 'cosine', 'embedding_model': EMBEDDING_MODEL})
    if result.metadata.get('embedding_model') != EMBEDDING_MODEL:
        raise ValueError('Embedding model changed. Restore the original model or rebuild the database.')
    return result


def embedder():
    from sentence_transformers import SentenceTransformer
    options = {'cache_folder': str(ROOT / '.model_cache')}
    try:
        return SentenceTransformer(EMBEDDING_MODEL, local_files_only=True, **options)
    except OSError:
        return SentenceTransformer(EMBEDDING_MODEL, **options)

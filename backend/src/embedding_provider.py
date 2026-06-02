"""Ленивая загрузка модели sentence-transformers для Celery worker."""

from src.constants.embeddings import EMBEDDING_MODEL_NAME, EMBEDDING_PASSAGE_PREFIX

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def encode_passage(text: str) -> list[float]:
    prefixed = f'{EMBEDDING_PASSAGE_PREFIX}{text}'
    vector = _get_model().encode(prefixed, normalize_embeddings=True)
    return vector.tolist()

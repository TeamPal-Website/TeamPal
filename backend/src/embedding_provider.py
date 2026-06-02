from typing import Protocol, runtime_checkable

from src.constants.embeddings import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_PASSAGE_PREFIX,
    EMBEDDING_QUERY_PREFIX,
)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Контракт кодировщика текста в нормализованный вектор."""

    def encode_query(self, text: str) -> list[float]:
        """Кодирует текст-запрос (резюме) в вектор.

        :param text: Исходный текст резюме.
        :returns: Нормализованный вектор.
        :rtype: list[float]
        """
        ...

    def encode_passage(self, text: str) -> list[float]:
        """Кодирует текст-документ (вакансию) в вектор.

        :param text: Исходный текст вакансии.
        :returns: Нормализованный вектор.
        :rtype: list[float]
        """
        ...


class SentenceTransformerProvider:
    """Реализация ``EmbeddingProvider`` на базе multilingual-e5 (sentence-transformers).

    Модель асимметрична: запросы кодируются с префиксом ``query:``,
    документы — с префиксом ``passage:``. Модель загружается лениво при
    первом обращении и переиспользуется в рамках процесса воркера.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        """Сохраняет имя модели без немедленной загрузки.

        :param model_name: Идентификатор модели sentence-transformers.
        """
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        """Лениво загружает и кэширует модель sentence-transformers.

        :returns: Экземпляр ``SentenceTransformer``.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _encode(self, prefix: str, text: str) -> list[float]:
        """Кодирует текст с заданным префиксом в нормализованный вектор.

        :param prefix: Префикс модели (``query:`` или ``passage:``).
        :param text: Исходный текст.
        :returns: Нормализованный вектор.
        :rtype: list[float]
        """
        vector = self._get_model().encode(f'{prefix}{text}', normalize_embeddings=True)
        return vector.tolist()

    def encode_query(self, text: str) -> list[float]:
        """Кодирует текст резюме (запрос) с префиксом ``query:``."""
        return self._encode(EMBEDDING_QUERY_PREFIX, text)

    def encode_passage(self, text: str) -> list[float]:
        """Кодирует текст вакансии (документ) с префиксом ``passage:``."""
        return self._encode(EMBEDDING_PASSAGE_PREFIX, text)


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Возвращает провайдер эмбеддингов по умолчанию (синглтон процесса).

    Единственная точка, где выбирается конкретная реализация. Для смены
    модели достаточно вернуть здесь другой объект, реализующий протокол.

    :returns: Активный провайдер эмбеддингов.
    :rtype: EmbeddingProvider
    """
    global _provider
    if _provider is None:
        _provider = SentenceTransformerProvider()
    return _provider


def encode_passage(text: str) -> list[float]:
    """Кодирует текст вакансии (документ) через провайдер по умолчанию.

    :param text: Исходный текст вакансии.
    :returns: Нормализованный вектор.
    :rtype: list[float]
    """
    return get_embedding_provider().encode_passage(text)


def encode_query(text: str) -> list[float]:
    """Кодирует текст резюме (запрос) через провайдер по умолчанию.

    :param text: Исходный текст резюме.
    :returns: Нормализованный вектор.
    :rtype: list[float]
    """
    return get_embedding_provider().encode_query(text)

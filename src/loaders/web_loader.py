"""Web page document loader using LangChain's WebBaseLoader."""
from typing import List

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

from src.core.constants import FileType
from src.core.exceptions import DocumentLoadException
from src.loaders.base_loader import BaseDocumentLoader
from src.utils.logger import get_logger
from src.utils.validators import validate_url

logger = get_logger(__name__)


class WebLoader(BaseDocumentLoader):
    """Fetch and parse HTML content from a URL."""

    file_type = FileType.URL.value

    def __init__(self, source: str, **kwargs) -> None:
        super().__init__(source, **kwargs)
        validate_url(source)

    def _load(self) -> List[Document]:
        try:
            loader = WebBaseLoader(
                web_paths=[self.source],
                requests_kwargs={"timeout": 30},
            )
            # Provide a friendlier user agent
            loader.requests_per_second = 2
            documents = loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to fetch URL: {self.source}",
                details={"source": self.source},
                cause=exc,
            ) from exc

        # Strip excess whitespace produced by HTML extraction
        for d in documents:
            d.page_content = "\n".join(
                line.strip() for line in d.page_content.splitlines() if line.strip()
            )
        documents = [d for d in documents if d.page_content]
        logger.debug("Web loaded", url=self.source, chars=sum(len(d.page_content) for d in documents))
        return documents

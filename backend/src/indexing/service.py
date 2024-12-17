from pathlib import Path
import sys

from dataclasses import dataclass
import logging
from typing import Optional, List

from haystack import Pipeline
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import TextFileToDocument, PyPDFToDocument, MarkdownToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from haystack.document_stores.types import DuplicatePolicy

from common.file_manager import FileManager
from common.pipeline_loader import load_pipeline
from common.config import settings


logger = logging.getLogger(__name__)

"""@component
class FilePathRemover:
    @component.output_types(documents=List[Document])
    def run(self, docs: List[Document]):
        documents_copy = copy.deepcopy(documents)
    
        for doc in documents_copy:
            del doc.meta["file_path"]
        return {"documents": documents_copy}"""

@dataclass
class IndexingConfig:
    document_store: OpenSearchDocumentStore
    pipeline_filename: str = "index.yml"
    embedder_model: str = "intfloat/multilingual-e5-base"
    split_by: str = "word"
    split_length: int = 250
    split_overlap: int = 30
    writer_policy: DuplicatePolicy = DuplicatePolicy.SKIP

def create_indexing_pipeline(config: IndexingConfig) -> Pipeline:
    """
    Create and configure an indexing pipeline for processing various file types.

    This function sets up a Haystack pipeline that performs the following steps:
    1. Routes files based on type (text, PDF, Markdown)
    2. Converts files to documents
    3. Joins multiple documents
    4. Cleans the documents
    5. Splits documents into smaller chunks
    6. Embeds the document chunks using SentenceTransformers
    7. Writes the processed documents to the document store

    Args:
        config (IndexingConfig): Configuration object containing settings for the indexing pipeline.

    Returns:
        Pipeline: A configured Haystack pipeline ready for indexing documents.

    Raises:
        None
    """
    p = Pipeline()
    
    # File type router to direct files to appropriate converters
    p.add_component(
        instance=FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/markdown"]), 
        name="file_type_router"
    )

    # File converters
    p.add_component(instance=TextFileToDocument(), name="text_file_converter")
    p.add_component(instance=PyPDFToDocument(), name="pdf_file_converter")
    p.add_component(instance=MarkdownToDocument(), name="markdown_converter")

    # Document processing
    p.add_component(instance=DocumentJoiner(join_mode="concatenate"), name="document_joiner")
    p.add_component(instance=DocumentCleaner(), name="document_cleaner")
    p.add_component(instance=DocumentSplitter(
        split_by=config.split_by, 
        split_length=config.split_length, 
        split_overlap=config.split_overlap
    ), name="document_splitter")

    # Embedding and document indexing
    if settings.use_openai_embedder:
        p.add_component(
            instance=OpenAIDocumentEmbedder(),
            name="document_embedder"
        )
    else:
        p.add_component(
            instance=SentenceTransformersDocumentEmbedder(model=config.embedder_model),
            name="document_embedder"
        )

    p.add_component(
        instance=DocumentWriter(document_store=config.document_store, policy=config.writer_policy),
        name="document_writer"
    )

    # Connect components to each other
    p.connect("file_type_router.text/plain", "text_file_converter.sources")
    p.connect("file_type_router.application/pdf", "pdf_file_converter.sources")
    p.connect("file_type_router.text/markdown", "markdown_converter.sources")

    p.connect("text_file_converter", "document_joiner.documents")
    p.connect("pdf_file_converter", "document_joiner.documents")
    p.connect("markdown_converter", "document_joiner.documents")

    p.connect("document_joiner.documents", "document_cleaner.documents")
    p.connect("document_cleaner.documents", "document_splitter.documents")
    p.connect("document_splitter.documents", "document_embedder.documents")
    p.connect("document_embedder.documents", "document_writer.documents")
    
    return p

class IndexingService:
    def __init__(self, document_store):
        self.config = IndexingConfig(document_store=document_store)
        self.pipeline = None

        if settings.pipelines_from_yaml:
            try:
                self.pipeline = load_pipeline(settings.pipelines_dir, self.config.pipeline_filename)
            except Exception as e:
                logger.warning(f"Failed to load pipeline from YAML: {e}. Falling back to default pipeline.")

        if self.pipeline is None:
            self.pipeline = create_indexing_pipeline(self.config)

        #print(f"\n--- Indexing Pipeline ---\n{self.pipeline.dumps()}")

        self.file_manager = FileManager()

    def index_files(self, path: Optional[str] = None):
        if self.pipeline is None:
            raise ValueError("Indexing pipeline has not been initialized")
 
        # If path is provided, index that single file, otherwise index all files
        sources = [path] if path and Path(path).is_file() else self.file_manager.file_paths

        if not sources:
            logger.info("No files to index")
            return

        logger.info(f"Indexing files: {sources}")

        # Here "file_type_router" has to match the pipeline component definition!
        result = self.pipeline.run({"file_type_router": {"sources": sources}})

        logger.info(f"Indexing result: {result}")
        return result

    def save_uploaded_file(self, filename: str, contents: bytes) -> str:
        full_path = self.file_manager.save_file(filename, contents)
        # Index uploaded file synchronously
        self.index_files(full_path)
        return full_path

    def rescan_files_and_paths(self) -> List[str]:
        return self.file_manager.add_files_and_paths()

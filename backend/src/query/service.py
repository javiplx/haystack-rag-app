from pathlib import Path
import sys

from dataclasses import dataclass
import logging
from typing import Optional

from haystack import Pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.joiners import DocumentJoiner
from haystack.components.builders import PromptBuilder
from haystack.components.generators.openai import OpenAIGenerator
from haystack.components.builders.answer_builder import AnswerBuilder
from haystack_integrations.components.retrievers.opensearch import OpenSearchBM25Retriever, OpenSearchEmbeddingRetriever
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore

from common.config import settings
from common.pipeline_loader import load_pipeline
from query.serializer import serialize_query_result


logger = logging.getLogger(__name__)

@dataclass
class QueryConfig:
    document_store: OpenSearchDocumentStore
    pipeline_filename: str = "query.yml"
    embedder_model: str = "intfloat/multilingual-e5-base"
    llm_name: str = "gpt-4o"
    prompt_template: str = """
    Given the following context, answer the question.
    Context:
    {% for document in documents %}
        {{ document.content }}
    {% endfor %}
    Question: {{query}}
    Answer:
    """

def create_query_pipeline(config: QueryConfig) -> Pipeline:
    p = Pipeline()

    if settings.use_openai_embedder:
        p.add_component(
            instance=OpenAITextEmbedder(),
            name="query_embedder"
        )
    else:
        p.add_component(
            instance=SentenceTransformersTextEmbedder(model=config.embedder_model),
            name="query_embedder"
        )

    p.add_component(
        instance=OpenSearchBM25Retriever(document_store=config.document_store), 
        name="bm25_retriever"
    )  # BM25 Retriever

    p.add_component(
        instance=OpenSearchEmbeddingRetriever(document_store=config.document_store), 
        name="embedding_retriever"
    )  # Embedding Retriever (OpenSearch)

    p.add_component(
        instance=DocumentJoiner(join_mode="concatenate"), 
        name="document_joiner"
    )  # Document Joiner

    p.add_component(
        instance=PromptBuilder(template=config.prompt_template), 
        name="prompt_builder"
    )  # Prompt Builder

    p.add_component(
        instance=AnswerBuilder(), 
        name="answer_builder"
    )  # Answer Builder

    if settings.generator == "openai":
        p.add_component(
            instance=OpenAIGenerator(model=config.llm_name),
            name="llm"
        )
    else:
        raise ValueError(f"Invalid generator: {settings.generator}")

    # Connect components to each other
    p.connect("bm25_retriever.documents", "document_joiner.documents")
    p.connect("query_embedder.embedding", "embedding_retriever.query_embedding")
    p.connect("embedding_retriever.documents", "document_joiner.documents")
    p.connect("document_joiner.documents", "prompt_builder.documents")
    p.connect("prompt_builder.prompt", "llm.prompt")
    p.connect("embedding_retriever.documents", "answer_builder.documents")
    p.connect("llm.replies", "answer_builder.replies")

    return p

class QueryService:
    def __init__(self, document_store):
        self.config = QueryConfig(document_store=document_store)
        self.pipeline = None

        if settings.pipelines_from_yaml:
            try:
                self.pipeline = load_pipeline(settings.pipelines_dir, self.config.pipeline_filename)
            except Exception as e:
                logger.warning(f"Failed to load pipeline from YAML: {e}. Falling back to default pipeline.")

        if self.pipeline is None:
            self.pipeline = create_query_pipeline(self.config)

        #print(f"\n--- Query Pipeline ---\n{self.pipeline.dumps()}")

    def search(self, query: str, filters: Optional[dict] = None):
        if self.pipeline is None:
            raise ValueError("Query pipeline has not been initialized")

        # Component names here should match pipeline definition!
        pipeline_params = {
            "bm25_retriever": {"query": query, "filters": filters},
            "query_embedder": {"text": query},
            "answer_builder": {"query": query},
            "prompt_builder": {"query": query}
        }

        logger.info("Running query pipeline...")

        # Run the query pipeline
        results = self.pipeline.run(pipeline_params)

        logger.debug(f"Query pipeline.run() results:\n{results}")

        answer = results['answer_builder']['answers'][0]

        return answer

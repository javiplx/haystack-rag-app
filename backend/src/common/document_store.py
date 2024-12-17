import os
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from common.config import settings


def initialize_document_store():
    embedding_dim = 1536 if settings.use_openai_embedder else 768

    return OpenSearchDocumentStore(
        hosts=settings.opensearch_host,
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=True,
        verify_certs=False,  # You might want to set this to True in production
        ssl_assert_hostname=False,  # You might want to set this to True in production
        ssl_show_warn=False,
        embedding_dim=embedding_dim,
    )

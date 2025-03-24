
This directory contains the initial iteration to deploy the haystack RAG sample application

A no-brain installation procedure would run these commands
```
kubectl create ns haystack
kubectl config set-context --current --namespace haystack

helm install opensearch opensearch/opensearch \
    --set singleNode=true \
    --set 'extraEnvs[0].name=OPENSEARCH_INITIAL_ADMIN_PASSWORD' \
    --set 'extraEnvs[0].value=Y0ur.password_here'

kubectl create secret generic opensearch-password \
    --from-literal OPENSEARCH_PASSWORD=Y0ur.password_here \
    --from-literal OPENAI_API_KEY=sk-proj-999

helm install haystack .
```
although images must be build in advance
```
docker build -t haystack-rag-query:1.0.0 -f backend/Dockerfile.query backend
docker build -t haystack-rag-index:1.0.0 -f backend/Dockerfile.indexing backend
docker build -t haystack-rag-frontend:2.0.0 -f frontend/Dockerfile.frontend frontend \
    --build-arg REACT_APP_HAYSTACK_API_URL=http://rag.localdomain:8080/api
```

#!/bin/bash

echo "Starting Ollama setup..."

# Check if Ollama is ready
wait_for_ollama() {
    echo "Waiting for Ollama to be ready..."
    while ! ollama list >/dev/null 2>&1; do
        sleep 1
    done
    echo "Ollama is ready!"
}

# Start Ollama service in the background
echo "Starting Ollama service..."
ollama serve &

# Wait for Ollama to be ready
wait_for_ollama

if ! ollama list | grep -i "llama3.2:1b"; then
    # Pull the model (TODO: Is this blocking/synchronous?)
    echo "Pulling llama3.2:1b model..."
    ollama pull llama3.2:1b
else
    echo "Model llama3.2:1b already in the local cache."
fi

# Keep the script running to keep the container alive
echo "Ollama setup complete. Keeping container running..."
tail -f /dev/null

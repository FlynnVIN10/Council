#!/bin/bash

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama via Homebrew..."
    brew install ollama
fi

# Pull recommended model
echo "Pulling phi3:mini model..."
ollama pull phi3:mini

echo "Setup complete!"
echo "To start the Ollama server: ollama serve"
echo "Run this in a separate terminal before using the project."


# Use the official Ollama base image
FROM ollama/ollama:latest

# Pull your model when building
RUN ollama pull gpt-oss:20b

# Expose the Ollama API port
EXPOSE 11434

# Start the Ollama server
CMD ["ollama", "serve"]


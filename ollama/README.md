# Ollama GPT-OSS:20b

Run Ollama with GPT-OSS:20b model exposed on localhost.

## Quick Start

1. Start the container:
   ```bash
   docker-compose up -d
   ```

2. Pull the model:
   ```bash
   docker exec ollama-gpt-oss ollama pull gpt-oss:20b
   ```

3. Access the API at `http://localhost:11434`

## Usage

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss:20b",
  "prompt": "Hello, how are you?"
}'
```


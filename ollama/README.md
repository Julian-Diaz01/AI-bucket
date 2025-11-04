# Ollama GPT-OSS:20b

Run Ollama with GPT-OSS:20b model exposed on localhost.

## Prerequisites

**Important:** The gpt-oss:20b model requires ~13GB of memory. Since you're using WSL 2 backend, configure memory limits in `.wslconfig`:

1. Create/edit `.wslconfig` in your home directory (`C:\Users\<YourUsername>\.wslconfig`)
2. Set `memory=32GB` (or at least 16GB minimum)
3. Restart WSL: `wsl --shutdown` (then restart Docker Desktop)

Example `.wslconfig`:
```ini
[wsl2]
memory=32GB
processors=8
swap=8GB
```

After updating `.wslconfig`, restart WSL 2:
```powershell
wsl --shutdown
```
Then restart Docker Desktop.

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
curl http://localhost:11434/api/generate -d '{"model":"gpt-oss:20b","prompt":"Hello, how are you?"}'
```

## Configuration

- **Memory Limit**: 32GB (set in `.wslconfig` for WSL 2)
- **CPU Limit**: 8 cores (configurable in docker-compose.yml)
- **Models Storage**: `D:\.ollama` (hostPath mount)

**Note:** With WSL 2 backend, resource limits are controlled by `.wslconfig`, not Docker Desktop settings.


# Ollama Setup Guide for MeetingMind

This guide covers how to set up Ollama locally to run the Llama 3 model, which powers the summary and action item generation in the MeetingMind backend.

## 1. Install Ollama

Download and install Ollama for your operating system:

- **macOS / Windows / Linux:** Download from the [official Ollama website](https://ollama.com/download).

Alternatively, on macOS with Homebrew, you can run:

```bash
brew install --cask ollama
```

On Linux, you can use the installation script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## 2. Start the Ollama Service

If you installed Ollama as a desktop app on macOS or Windows, open the app to start the background service. You should see the Ollama icon in your system tray/menu bar.

If you are running it manually from the terminal, start the server:

```bash
ollama serve
```

_(Leave this terminal window open if running manually)._

## 3. Pull the Llama 3 Model

With the service running, open a new terminal and download the `llama3` model:

```bash
ollama run llama3
```

This will download the model (approx 4.7GB). Once downloaded, you will drop into an interactive prompt. You can type a test message like `Hello` to ensure it responds. Press `Ctrl+D` or type `/bye` to exit the prompt. The model is now cached locally.

## 4. Verify Local API Connection

Ollama exposes a local REST API by default on port `11434`. You can test if it's responding with curl:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

You should receive a JSON response containing the generated text.

## 5. Configure the Backend

In your FastAPI backend `.env` file, ensure you have the following configured:

```env
OLLAMA_API_URL=http://localhost:11434/api/generate
```

The backend will use this URL to send prompts to your local Llama 3 model when processing meetings.

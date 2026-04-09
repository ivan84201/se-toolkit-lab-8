### Product name - LLM_File_Manager_Bot

### Description:

stores user files, tags them for easier navigation, answer questions based on these files.

### Demo:

![demo1](1.png)

![demo2](2.png)

### Product context:

End users - anyone that needs to efficiently store and access medium amount of information for personal use. For example, students.

Problem - efficient handling of diverse files.

Solution - add tags to files using llm for efficient navigation. Then, llm can navigate these files and extract answers to user questions.

### Features:

file storage, automated tagging system, llm answers question based on user files.

### Usage:

find @LLMFileManagerBot in telegram, upload your files, ask questions in plain text.

### Deployment:

## OS required - Ubuntu 24.04

## Required tools:
docker
git
JSON
uv
Qwen LLM provider

## Setup (paste commands to terminal 1 by 1):
git clone https://github.com/ivan84201/se-toolkit-hackathon
cd se-toolkit-hackathon
uv sync --dev
cp .env.docker.example .env.docker.secret
## fill in .env.docker.secret with your data (see comments and values in <>)
cd nanobot
uv run nanobot onboard -c config.json
## fill in nanobot config.json
## Set up the custom provider (any OpenAI-compatible endpoint) and point it to the Qwen Code API:
agents.defaults.workspace ./workspace
agents.defaults.model coder-model
agents.defaults.provider custom
providers.custom.apiKey your QWEN_CODE_API_KEY from .env.docker.secret
providers.custom.apiBase http://localhost:42005/v1
## To start docker containers:
docker compose --env-file .env.docker.secret up -d
docker compose --env-file .env.docker.secret build
docker compose --env-file .env.docker.secret build # second time if postgres crashed
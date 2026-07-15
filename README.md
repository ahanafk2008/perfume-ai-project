# Perfume AI Assistant

AI-powered chatbot for perfume businesses using FastAPI, Google Gemini, SQLite, and the Meta Graph API.

## Features
- AI customer support
- Product recommendations
- FAQ answering
- Facebook Messenger integration
- Instagram messaging integration
- SQLite product database

## Tech Stack
- Python
- FastAPI
- Google Gemini
- SQLite
- Meta Graph API

## Installation

pip install -r requirements.txt

## Run

uvicorn app.main:app --reload

## Project Structure

app/
tests/
data/

## Environment Variables

Create a .env file:

GEMINI_API_KEY=...
META_ACCESS_TOKEN=...

## License

MIT

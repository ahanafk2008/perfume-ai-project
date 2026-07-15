# Perfume AI Assistant

An AI-powered chatbot for perfume businesses built with **FastAPI**, **Google Gemini**, **SQLite**, and the **Meta Graph API**. It automates customer support, answers product questions, and provides intelligent fragrance recommendations through Facebook Messenger and Instagram.

## ✨ Features

- 🤖 AI-powered customer support
- 💬 Natural language conversations
- 🌸 Perfume recommendations
- 📦 Product search and information
- 📱 Facebook Messenger integration
- 📷 Instagram Messaging integration
- 🗄️ SQLite product database
- ⚡ FastAPI REST API

## 🛠️ Tech Stack

- Python
- FastAPI
- Google Gemini API
- SQLite
- Meta Graph API

## 📁 Project Structure

```
app/
data/
tests/
requirements.txt
```

## 🚀 Installation

```bash
git clone https://github.com/ahanafk2008/perfume-ai-project.git
cd perfume-ai-project
pip install -r requirements.txt
```

## ⚙️ Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key
META_ACCESS_TOKEN=your_access_token
```

## ▶️ Run

```bash
uvicorn app.main:app --reload
```

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue, suggest improvements, or submit a pull request.

## 📄 License

This project is licensed under the MIT License.

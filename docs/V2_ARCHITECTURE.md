# V2 Architecture

## Overview
The Perfume AI assistant has been refactored from a CLI-centered architecture to a **service-oriented architecture**. This intermediate step (V2 Bootstrap) introduces the necessary abstractions (Services and Repositories) without altering any existing business logic, algorithms, or database queries.

The primary goal of this architecture is to decouple the input/output mechanism (CLI) from the core workflow, allowing for future integration with web frameworks (like FastAPI) and external platforms (like Facebook Messenger) seamlessly.

## Module Responsibilities

### `app/core/`
Contains application-wide utilities and configurations.
- `exceptions.py`: Base and custom exceptions for structured error handling.

### `app/api/`
*(Currently scaffolded)*
Will handle incoming web requests and route them to the appropriate services. This layer will replace the CLI as the primary entry point when FastAPI is integrated.

### `app/services/`
The orchestration and business logic layer.
- `chat.py (ChatService)`: Orchestrates the main flow. It receives the raw user input, coordinates with intent detection, retrieves products, and invokes the AI models.
- `intent.py`: *(Scaffolded)* Future home for advanced intent routing (e.g., using LLMs or fastText).
- `search.py`: *(Scaffolded)* Future home for orchestrating complex search logic (e.g., vector search).
- `ai.py`: *(Scaffolded)* Future home for abstracting different LLM providers (Ollama vs. Gemini).

### `app/repositories/`
The data access layer.
- `product_repository.py (ProductRepository)`: Wraps database queries. It provides an abstraction layer so that services do not need to interact directly with SQLite or SQL queries.

## Dependency Direction
The dependency flow strictly points inward toward the core and data models:
`CLI (main.py) / API` → `Services (ChatService)` → `Repositories (ProductRepository)` → `Database`

## Migration Notes for Future Steps
- **Web Integration:** A FastAPI app should be created inside `app/api/` that instantiates `ChatService` and processes webhook payloads instead of CLI inputs.
- **State Management:** `app/conversation.py` is still using an in-memory dictionary. In future updates, this should be replaced by a Redis-backed session store, abstracted behind a `SessionRepository` or similar.
- **Search Optimization:** The logic in `ProductRepository` currently executes synchronous SQLite `LIKE` queries. This should be migrated to FTS5 or an asynchronous driver without needing to modify the `ChatService`.

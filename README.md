# FilmGuide AI Agent

An intelligent movie recommendation system powered by AI agents that provides personalized film suggestions and engages in natural conversations about movies, actors, genres, and more.

FilmGuide is built on a multi-agent architecture using the `uagents` framework. The system demonstrates how to build a production-ready AI agent application with the following patterns:

## Core Concepts

### Agent Architecture
Agents are autonomous software entities that can send and receive messages, process data, and perform actions. In this system, we use three specialized agents:

1. **Processing Agent** (Movie Agent) - Specialized in AI-powered content generation
2. **Gateway Agent** (Backend Agent) - Handles HTTP requests and orchestrates communication
3. **Trailer Agent** - Specialized in finding movie trailers and video content

---

## Architecture

```
┌─────────────┐
│  Web App    │
│  (Frontend) │
└──────┬──────┘
       │ HTTP REST
       ▼
┌──────────────────────┐
│   Backend Agent      │  ← Manages conversations, REST API
│   Port: 8000         │  ← Maintains memory & context
└──────┬───────────────┘
       │ Message
       ▼
┌──────────────────────┐
│   Movie Agent        │  ← Generates recommendations
│   Port: 5050         │  ← Uses AI + dataset
└──────────────────────┘
       │ Message
       ▼
┌──────────────────────┐
│   Trailer Agent      │  ← Finds movie trailers
│   Port: 5051         │  ← Uses AI + dataset
└──────────────────────┘
```

### Components

#### **1. Backend Agent** 
**Role**: API Gateway & Orchestrator

This agent serves as the entry point for external requests (web app). It implements the **Gateway Pattern** by:

- **HTTP Interface**: Exposes REST endpoints for synchronous communication
- **Message Translation**: Converts HTTP requests into agent messages
- **Request Management**: Tracks pending requests and manages timeouts
- **State Management**: Maintains conversation history and user context
- **Security**: Validates credentials before processing

**Key Design Pattern**: Gateway/Orchestrator pattern - handles protocol translation and request lifecycle.

#### **2. Movie Agent** 
**Role**: Specialized Processing Agent

This agent is responsible for AI-powered content generation. It implements the **Worker Agent Pattern**:

- **Single Responsibility**: Focuses solely on generating recommendations
- **AI Integration**: Interfaces with external AI services (ASI One API)
- **Data Enhancement**: Enriches responses using curated datasets
- **Persona Implementation**: Maintains consistent personality and tone
- **Asynchronous Processing**: Handles multiple requests independently

**Key Design Pattern**: Worker/Specialist pattern - dedicated agent for a specific task.

#### **3. Trailer Agent** 
**Role**: Video Content Specialist

This agent specializes in finding and providing movie trailer information. It implements the **Content Specialist Pattern**:

- **Trailer Discovery**: Finds trailer links for specific movies from the dataset
- **Similar Movie Suggestions**: Provides alternative recommendations when exact matches aren't found
- **Video Dataset Integration**: Uses curated video links from the movies dataset
- **AI-Powered Matching**: Leverages ASI One API for intelligent trailer matching

**Key Design Pattern**: Content Specialist pattern - dedicated agent for video content discovery.

---
### Dependencies

Install the following dependencies:

```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- `uagents>=0.22.5` - Multi-agent framework for building decentralized applications
- `openai>=1.0.0` - OpenAI API client (optional, using ASI One)
- `flask>=2.3.0` - Web framework (used by uagents internally)
- `flask-cors>=4.0.0` - CORS support for cross-origin requests
- `requests>=2.31.0` - HTTP library for API calls
- `python-dotenv>=1.0.0` - Environment variable management
- `pandas>=2.3.3` - Data manipulation and CSV processing

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)
- ASI One API key 
- AGENTVERSE API key


## Example Prompts
- "Recommend me movies about Bitcoin"
- "Tell me about Vitalik Buterin documentaries"
- "Tell me more about that first one"
- "Where can I watch crypto documentaries"
- "Find the trailer for The Matrix"
- "Show me trailers for sci-fi movies"
- "I want to watch the trailer for Inception"

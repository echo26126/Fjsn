# AI Integration Specification

## Goal
Switch the "AI Q&A" (问数) and "Suggestion" (建议) capabilities from mock implementations to a real inference service (LLM) and establish a closed-loop evaluation system.

## Current State
- `backend/routers/agent.py` uses `MOCK_ANSWERS` dictionary to return static responses.
- `frontend/src/components/AiAssistant.vue` uses local `mockAnswers` and `setTimeout` to simulate latency.

## Target Architecture

### Backend (`backend/`)
1.  **LLM Service (`services/llm_service.py`)**:
    - Encapsulate LLM API calls (e.g., DeepSeek/OpenAI compatible).
    - Handle prompt engineering for:
        - Natural Language to SQL (NL2SQL).
        - Data analysis and summarization.
    - Support configuration via environment variables (API Key, Base URL, Model Name).

2.  **Database Service (`services/db_service.py`)**:
    - Execute generated SQL queries against the database (Doris/PostgreSQL/Mock DB).
    - Return query results in a structured format (JSON/Pandas DataFrame).
    - For this phase, if a real DB is not available, we will implement a *smart mock* that executes SQL on a local SQLite database populated with sample data, or validates the SQL syntax without execution if no DB is present.

3.  **Agent Router (`routers/agent.py`)**:
    - Receive user question.
    - Call `LLM Service` to generate SQL.
    - Call `Database Service` to execute SQL.
    - Call `LLM Service` to generate final answer based on SQL results.
    - Return answer, SQL, and data to frontend.

### Frontend (`frontend/`)
1.  **API Integration**:
    - Update `src/api/index.ts` (or create `src/api/agent.ts`) to define `chat` and `suggest` API methods.
    - Update `src/components/AiAssistant.vue` to use the real API.
    - Remove local mock data.
    - Handle loading states and error messages.

### Evaluation
1.  **Evaluation Script (`evaluation/evaluate_ai.py`)**:
    - A Python script to run a set of test questions against the API.
    - Metrics:
        - **Success Rate**: API returns 200 OK.
        - **SQL Validity**: Generated SQL is valid (syntax check).
        - **Response Relevance**: (Manual review or LLM-based evaluation if possible).
    - Output: `evaluation/report.md`.

## Configuration
- `LLM_API_KEY`: API Key for the LLM provider.
- `LLM_BASE_URL`: Base URL for the LLM provider.
- `LLM_MODEL`: Model name (e.g., `deepseek-chat`).
- `DB_CONNECTION_STRING`: Connection string for the database.

## Risks & Mitigation
- **Risk**: Real DB not available.
  - **Mitigation**: Use SQLite with sample data or mock the DB execution layer while keeping the LLM generation real.
- **Risk**: LLM API costs/availability.
  - **Mitigation**: Use a low-cost model or a local model if available. (Assuming user has access or we provide instructions).

## Deliverables
1.  Updated backend code with real LLM integration.
2.  Updated frontend code using real API.
3.  Evaluation script and report.
4.  Integration documentation (`docs/AI_INTEGRATION.md`).

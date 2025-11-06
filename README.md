# Pydantic-AI Streamable HTTP Tool Server and Client

This project demonstrates a client-server architecture where a large language model (LLM) powered agent can utilize a set of tools exposed by a remote server. The communication between the client and server is handled over HTTP, and the server can stream responses back to the client. The project also showcases a tool approval mechanism, where the client can require user confirmation before executing a specific tool.

## Features

*   **Remote Tool Execution:** An LLM agent can use tools defined on a separate server.
*   **Streaming Support:** The server can stream data to the client, allowing for real-time updates.
*   **Tool Approval Workflow:** The server can flag certain tools as requiring approval, and the client can implement a workflow to get user consent before execution.
*   **User and Note Management:** The server provides tools for user registration, login, and note-taking.
*   **Web Search:** The server includes a tool to perform web searches using DuckDuckGo.
*   **Async Support:** Both the client and server are built using asynchronous Python libraries.

## Requirements

The project dependencies are listed in the `pyproject.toml` file. They can be installed using a package manager like `pip`.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install "duckduckgo-search>=8.1.1" "fastapi>=0.120.4" "jinja2>=3.1.6" "jupyter>=1.1.1" "pydantic-ai>=0.1.0" "starlette>=0.49.3" "uvicorn>=0.38.0"
    ```
2.  **Set up environment variables:**
    Create a `.env` file with the following variables:
    ```
    GROQ_API_KEY=<your_groq_api_key>
    GROQ_MODEL_NAME=<your_groq_model_name>
    LOGFIRE_API_KEY=<your_logfire_api_key>
    ```
3.  **Start the server:**
    ```bash
    python streamable_http_server.py
    ```
4.  **Run the client:**
    In a separate terminal, run:
    ```bash
    python mcp_streamable_http_client.py
    ```

## How to Use

Once the client is running, you can interact with the agent by typing in the terminal. Here are some examples:

*   **Register a user:** `register a new user with username "testuser" and password "password123"`
*   **Log in:** `login with username "testuser" and password "password123"`
*   **Save a note:** `save a note with topic "shopping" and content "milk, eggs, bread"`
    *   This will trigger the approval workflow. You will be prompted to approve the tool call.
*   **Retrieve a note:** `get the note with topic "shopping"`
*   **Search the web:** `search for "latest news on AI"`

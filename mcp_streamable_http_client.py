import os
import asyncio
from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from dotenv import load_dotenv
import logfire

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
logfire.instrument_pydantic_ai()

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
model = GroqModel(
    os.getenv("GROQ_MODEL_NAME"),
    provider=GroqProvider(api_key=os.getenv("GROQ_API_KEY"))
)
agent = Agent(model, toolsets=[server], output_type=[str, DeferredToolRequests])

async def main():
    history = []
    while True:
        try:
            query = input("You: ")
            if query.lower() in ["exit", "quit"]:
                break

            result = await agent.run(query, message_history=history)

            if isinstance(result.output, DeferredToolRequests):
                for req in result.output.requests:
                    print(f"\nApproval required for tool: {req.tool}")
                    print(f"Arguments: {req.tool_args}")
                    approve = input("Do you approve this tool call? [y/n]: ")
                    if approve.lower().startswith('y'): 
                        # Simulate backend execution (replace with DB insert as needed)
                        topic = req.tool_args.get("topic")
                        content = req.tool_args.get("content")
                        backend_result = f"Note on '{topic}' saved with content: {content}"
                        results = DeferredToolResults([{
                            "tool": req.tool,
                            "output": backend_result
                        }])
                        # Resume agent run with deferred results
                        next_result = await agent.run(
                            query,
                            message_history=history,
                            deferred_tool_results=results
                        )
                        print(f"LLM_Response: {next_result.output}")
                        history.extend(next_result.new_messages())
                    else:
                        print("Approval denied. Tool call skipped.")
                history.extend(result.new_messages())
            else:
                print(f"LLM_Response: {result.output}")
                history.extend(result.new_messages())

        except KeyboardInterrupt:
            break
    print("\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())

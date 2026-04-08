
import asyncio
from backend.agents.model_router import ModelRouter

async def test_router():
    router = ModelRouter()
    model = "ollama::llama3.2:latest"
    print(f"Testing {model}...")
    
    messages = [{"role": "user", "content": "Hello, are you working?"}]
    
    count = 0
    try:
        async for chunk in router.chat_stream(model, messages):
            print(f"Chunk: {chunk}")
            count += 1
    except Exception as e:
        print(f"Error: {e}")
        
    print(f"Total chunks: {count}")

if __name__ == "__main__":
    asyncio.run(test_router())

from client.async_client import MLXInferenceClient
import asyncio

async def main():
    client = MLXInferenceClient("http://127.0.0.1:8020/api/v1")

    try:
        await client.load_model("mlx-community/Llama-3.2-3B-Instruct-4bit")

        messages = [
            {"role": "system", "content": "you are a helpful assistant"},
            {"role": "user", "content": "tell me about quantum computing"}
        ]
        response = await client.chat_completion(messages)
        print(response["choices"][0]["message"]["content"])

    finally:
        await client.close()

asyncio.run(main())

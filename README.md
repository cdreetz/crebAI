# MLX Inference Server

A modular FastAPI-based server for running LLM inference on Apple Silicon (Mac Ultra) with MLX, allowing you to chat with models from your phone or other mobile devices.

## Features

- 📱 Mobile-friendly API for chatting with LLMs from your phone
- 🚀 Asynchronous processing with task scheduler
- 🍎 Optimized for Apple Silicon using MLX
- 🧩 Modular architecture for easy extension
- 📊 Task status tracking and management
- 🔄 Support for multiple concurrent inference requests
- 🔌 Simple client libraries for integration

## Architecture

The server is built with a modular architecture:

```
llm_inference_server/
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core configuration
│   ├── llm/             # LLM model interfaces
│   ├── models/          # Data models
│   ├── services/        # Business logic services
│   └── main.py          # Application entry point
├── client/              # Client libraries
├── tests/               # Test suite
└── docker/              # Docker configuration
```

## Installation

### Prerequisites

- Python 3.9+
- Apple Silicon Mac (M1/M2/M3 series)
- pip (Python package manager)

### Setup

1. Clone this repository:

```bash
git clone https://github.com/cdreetz/mlx-inference-server.git
cd mlx-inference-server
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:

```
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## Usage

### Running the Server

Start the server on your Mac Ultra:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://your-mac-ip:8000/api/v1`

### API Endpoints

The server exposes the following API endpoints:

- `POST /api/v1/text/generate` - Generate text from a prompt
- `POST /api/v1/chat/chat` - Generate a chat completion
- `GET /api/v1/tasks/{task_id}` - Get task status and result
- `GET /api/v1/models` - List available models
- `POST /api/v1/models/load` - Load a model into memory
- `POST /api/v1/models/unload/{model_name}` - Unload a model from memory
- `GET /api/v1/health` - Check API health

### Using the Client

#### Python Client

```python
from client.async_client import MLXInferenceClient
import asyncio

async def main():
    client = MLXInferenceClient("http://your-mac-ip:8000/api/v1")

    try:
        # Load a model
        await client.load_model("mlx-community/Llama-3.2-3B-Instruct-4bit")

        # Chat with the model
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about quantum computing."}
        ]
        response = await client.chat_completion(messages)
        print(response["choices"][0]["message"]["content"])

    finally:
        await client.close()

asyncio.run(main())
```

#### Mobile Client

For mobile apps, you can use the synchronous client:

```python
from client.mobile_client import MLXMobileClient

client = MLXMobileClient("http://your-mac-ip:8000/api/v1")

try:
    # Chat with the model
    response = client.chat_completion([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are the main features of Swift?"}
    ])
    print(response["choices"][0]["message"]["content"])

finally:
    client.close()
```

## Supported Models

The server uses MLX and `mlx-lm` to run models optimized for Apple Silicon. Supported models include:

- Llama 3.1, Llama 3.2 (4-bit quantized versions work best on Mac)
- Mistral
- Phi-3
- Qwen
- Any other model supported by MLX with a compatible architecture

## Mobile Integration

To integrate with a mobile app:

1. Create a native mobile app (iOS/Android)
2. Use the provided client library for your platform:
   - Swift client for iOS
   - Kotlin client for Android
   - Or use the Python client with frameworks like Kivy

For iOS, a simple API wrapper might look like:

```swift
import Foundation

class MLXClient {
    let baseURL: URL
    let session = URLSession.shared

    init(serverAddress: String) {
        self.baseURL = URL(string: "\(serverAddress)/api/v1")!
    }

    func sendMessage(_ message: String, completion: @escaping (Result<String, Error>) -> Void) {
        let chatEndpoint = baseURL.appendingPathComponent("chat/chat")
        var request = URLRequest(url: chatEndpoint)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let messages = [
            ["role": "system", "content": "You are a helpful assistant."],
            ["role": "user", "content": message]
        ]

        let body: [String: Any] = ["messages": messages]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        // First get the task ID
        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "MLXClient", code: 1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let taskID = json["task_id"] as? String {
                    self.pollForResult(taskID, completion: completion)
                } else {
                    completion(.failure(NSError(domain: "MLXClient", code: 2, userInfo: [NSLocalizedDescriptionKey: "Invalid response format"])))
                }
            } catch {
                completion(.failure(error))
            }
        }
        task.resume()
    }

    private func pollForResult(_ taskID: String, completion: @escaping (Result<String, Error>) -> Void) {
        let statusEndpoint = baseURL.appendingPathComponent("tasks/\(taskID)")
        let request = URLRequest(url: statusEndpoint)

        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "MLXClient", code: 1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let status = json["status"] as? String {

                    if status == "completed",
                       let result = json["result"] as? [String: Any],
                       let choices = result["choices"] as? [[String: Any]],
                       let firstChoice = choices.first,
                       let message = firstChoice["message"] as? [String: Any],
                       let content = message["content"] as? String {
                        completion(.success(content))
                    } else if status == "failed" {
                        completion(.failure(NSError(domain: "MLXClient", code: 3, userInfo: [NSLocalizedDescriptionKey: "Task failed"])))
                    } else {
                        // Still processing, poll again after a delay
                        DispatchQueue.global().asyncAfter(deadline: .now() + 0.5) {
                            self.pollForResult(taskID, completion: completion)
                        }
                    }
                } else {
                    completion(.failure(NSError(domain: "MLXClient", code: 2, userInfo: [NSLocalizedDescriptionKey: "Invalid response format"])))
                }
            } catch {
                completion(.failure(error))
            }
        }
        task.resume()
    }
}
```

## Performance Considerations

For optimal performance on Mac Ultra:

1. Use 4-bit quantized models when possible
2. Pre-load frequently used models at server startup
3. Set appropriate batch sizes based on your Mac's RAM
4. Consider setting a maximum concurrent task limit
5. For chat applications, stream responses if latency is important

## Model Configuration

Configure models in the `config.yaml` file:

```yaml
models:
  - name: llama-3-8b
    type: mlx
    path: mlx-community/Llama-3.2-8B-4bit
    preload: true
  - name: mistral-7b
    type: mlx
    path: mlx-community/Mistral-7B-v0.1-4bit
    preload: false
```

## Extending

### Adding New Model Backends

1. Create a new model class in `app/llm/models/`
2. Implement the `BaseLLMModel` interface
3. Register the model type in `app/llm/models/factory.py`

### Custom Endpoints

Add new endpoints in `app/api/endpoints/` and register them in `app/api/router.py`.

## License

[MIT License](LICENSE)

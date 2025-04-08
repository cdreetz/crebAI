# Chat App API Integration Specification

## Message Format

### Frontend Message Structure
Messages in the frontend are stored as objects with the following structure:
```javascript
{
  id: number,        // Timestamp-based unique identifier
  text: string,      // The actual message content
  sender: string     // Either "user" or "ai"
}
```

### API Message Format
When sending to the API, messages are transformed into this format:
```javascript
{
  messages: [
    {
      content: "You are a helpful assistant.",  // System message always included first
      role: "system"
    },
    {
      content: string,  // Message text
      role: string     // "user" for user messages, "assistant" for AI responses
    }
    // ... additional messages
  ]
}
```

## API Endpoint Configuration
- Base URL: `http://127.0.0.1:8000`
- Endpoint: `/api/v1/chat/chat`
- Method: `POST`
- Headers:
  ```javascript
  {
    "accept": "application/json",
    "Content-Type": "application/json"
  }
  ```

## Response Handling

### API Response Format
The API can respond in two ways:

1. Direct Response:
```javascript
{
  choices: [{
    message: {
      content: string  // The AI's response
    }
  }]
}
```

2. Task-based Response:
```javascript
{
  task_id: string  // ID for polling the result
}
```

### Task Polling (if applicable)
- Endpoint: `/api/v1/tasks/${taskId}`
- Method: `GET`
- Poll Interval: 1000ms (1 second)
- Maximum Attempts: 30
- Success Response:
  ```javascript
  {
    status: "completed",
    result: {
      choices: [{
        message: {
          content: string
        }
      }]
    }
  }
  ```

## Message Flow
1. User sends message through the UI
2. Frontend creates a message object with timestamp ID
3. Message is sent to the API with proper formatting
4. If direct response:
   - Parse response content
   - Display AI message in UI
5. If task-based response:
   - Begin polling for result
   - Once complete, parse and display response
   - If polling times out (30 attempts), show error
6. Any errors during the process are caught and displayed to the user

## Error Handling
- Network errors are caught and displayed
- Parsing errors show a generic message
- Polling timeout after 30 seconds
- Invalid responses are handled gracefully with fallback to stringified content

## Implementation Notes
- Uses Electron's IPC bridge for secure main/renderer process communication
- Messages are stored in React state
- Supports both synchronous and asynchronous (task-based) responses
- Includes proper error boundaries and fallbacks
- Maintains conversation history for context 
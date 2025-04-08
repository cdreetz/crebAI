// API calls to AI endpoint
const axios = require("axios");

// Local API endpoint
const API_ENDPOINT = "http://127.0.0.1:8000/api/v1/chat/chat";
const STREAMING_ENDPOINT = "http://127.0.0.1:8000/api/v1/chat/chat/stream";
const TASK_ENDPOINT = "http://127.0.0.1:8000/api/v1/tasks";

/**
 * Fetch a complete AI response
 * @param {Array} messages - Array of message objects with text and sender properties
 * @returns {Promise<Object>} - Response object with message property
 */
async function fetchAIResponse(messages) {
  try {
    // Convert our frontend message format to the API format
    const formattedMessages = [
      {
        content: "You are a helpful assistant.",
        role: "system",
      },
      ...messages.map((msg) => ({
        content: msg.text,
        role: msg.sender === "ai" ? "assistant" : "user",
      })),
    ];

    const response = await axios.post(
      API_ENDPOINT,
      {
        messages: formattedMessages,
        stream: false,
      },
      {
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
      },
    );

    // If the response contains a task_id, poll for the result
    if (response.data.task_id) {
      return await pollTaskResult(response.data.task_id);
    }

    // Extract the response content from the returned data
    return {
      message:
        response.data.choices?.[0]?.message?.content ||
        response.data.response ||
        response.data.message ||
        response.data,
    };
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

/**
 * Poll for a task result
 * @param {string} taskId - The ID of the task to poll for
 * @param {number} interval - Polling interval in milliseconds
 * @param {number} maxAttempts - Maximum number of polling attempts
 * @returns {Promise<Object>} - Response object with message property
 */
async function pollTaskResult(taskId, interval = 1000, maxAttempts = 60) {
  let attempts = 0;

  const poll = async () => {
    attempts++;

    try {
      const response = await axios.get(`${TASK_ENDPOINT}/${taskId}`, {
        headers: {
          accept: "application/json",
        },
      });

      const data = response.data;

      if (data.status === "completed") {
        return {
          message:
            data.result.choices?.[0]?.message?.content ||
            data.result.response ||
            data.result.message ||
            data.result,
        };
      } else if (data.status === "failed") {
        throw new Error(
          `Task failed: ${data.result?.error || "Unknown error"}`,
        );
      } else if (attempts >= maxAttempts) {
        throw new Error("Polling timeout - task did not complete in time");
      }

      // Wait for the next polling interval
      await new Promise((resolve) => setTimeout(resolve, interval));
      return poll();
    } catch (error) {
      console.error("Polling error:", error);
      throw error;
    }
  };

  return poll();
}

/**
 * Set up an EventSource for streaming responses
 * @param {Array} messages - Array of message objects with text and sender properties
 * @returns {EventSource} - EventSource instance for handling streaming events
 */
function setupStreamingResponse(messages) {
  try {
    // Convert our frontend message format to the API format
    const formattedMessages = [
      {
        content: "You are a helpful assistant.",
        role: "system",
      },
      ...messages.map((msg) => ({
        content: msg.text,
        role: msg.sender === "ai" ? "assistant" : "user",
      })),
    ];

    // Create the URL with the messages as a query parameter
    const url = new URL(STREAMING_ENDPOINT);
    url.searchParams.append("messages", JSON.stringify(formattedMessages));

    // Create and return an EventSource
    return new EventSource(url.toString());
  } catch (error) {
    console.error("Streaming setup error:", error);
    throw error;
  }
}

module.exports = {
  fetchAIResponse,
  setupStreamingResponse,
};

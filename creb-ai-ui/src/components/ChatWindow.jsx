import React, { useState, useRef, useEffect } from "react";
import Message from "./Message";

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI assistant. How can I help you today?",
      sender: "ai",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingEnabled, setStreamingEnabled] = useState(false);
  const messagesEndRef = useRef(null);
  const activeStreamRef = useRef(null);

  // Cleanup streaming on unmount
  useEffect(() => {
    return () => {
      if (activeStreamRef.current) {
        activeStreamRef.current.close();
        activeStreamRef.current = null;
      }
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = { id: Date.now(), text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // All messages except the initial greeting
    const messageHistory = messages.slice(1).concat(userMessage);

    try {
      if (streamingEnabled) {
        // Handle streaming response
        handleStreamingResponse(messageHistory);
      } else {
        // Handle regular response
        const response = await window.api.sendMessage(messageHistory);

        if (response.error) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              text: `Error: ${response.error}`,
              sender: "ai",
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              text: response.message,
              sender: "ai",
            },
          ]);
        }

        // Check if we got a task ID and need to poll for results
        if (response.taskId) {
          pollTaskStatus(response.taskId);
        } else {
          setIsLoading(false);
        }
      }
    } catch (error) {
      console.error("Failed to get response:", error);
      setIsLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: "Sorry, I couldn't process your request. Please try again.",
          sender: "ai",
        },
      ]);
    }
  };

  // Poll for task status if we get a task ID
  const pollTaskStatus = async (taskId, interval = 1000, maxAttempts = 60) => {
    let attempts = 0;

    const checkStatus = async () => {
      attempts++;

      try {
        const statusResponse = await window.api.getTaskStatus(taskId);

        if (statusResponse.status === "completed") {
          setIsLoading(false);
          setMessages((prev) => {
            // Find and update the task message
            return prev.map((msg) => {
              if (msg.text.includes(`Task ID: ${taskId}`)) {
                return {
                  ...msg,
                  text: statusResponse.result || "Task completed successfully",
                  sender: "ai",
                };
              }
              return msg;
            });
          });
          return;
        } else if (statusResponse.status === "failed") {
          setIsLoading(false);
          setMessages((prev) => {
            // Find and update the task message
            return prev.map((msg) => {
              if (msg.text.includes(`Task ID: ${taskId}`)) {
                return {
                  ...msg,
                  text: `Error: ${statusResponse.result?.error || "Task failed"}`,
                  sender: "ai",
                };
              }
              return msg;
            });
          });
          return;
        } else if (attempts >= maxAttempts) {
          setIsLoading(false);
          setMessages((prev) => {
            // Find and update the task message
            return prev.map((msg) => {
              if (msg.text.includes(`Task ID: ${taskId}`)) {
                return {
                  ...msg,
                  text: "Task is taking too long. Please check back later.",
                  sender: "ai",
                };
              }
              return msg;
            });
          });
          return;
        }

        // Continue polling
        setTimeout(checkStatus, interval);
      } catch (error) {
        console.error("Error polling task status:", error);
        setIsLoading(false);
        setMessages((prev) => {
          // Find and update the task message
          return prev.map((msg) => {
            if (msg.text.includes(`Task ID: ${taskId}`)) {
              return {
                ...msg,
                text: `Error checking task status: ${error.message}`,
                sender: "ai",
              };
            }
            return msg;
          });
        });
      }
    };

    // Start polling
    setTimeout(checkStatus, interval);
  };

  const handleStreamingResponse = (messageHistory) => {
    // Create a placeholder message that will be updated with streamed content
    const placeholderId = Date.now();
    
    // For debugging 
    console.log("Setting up streaming response with placeholder id:", placeholderId);

    // Add an empty message to start
    setMessages((prev) => {
      const newMessages = [
        ...prev,
        {
          id: placeholderId,
          text: "Loading...",  // Start with text rather than empty string
          sender: "ai",
          isStreaming: true,
        },
      ];
      console.log("Initial messages state with placeholder:", newMessages);
      return newMessages;
    });

    try {
      // Set up EventSource for streaming
      const eventSource = window.api.sendStreamingMessage(messageHistory);
      activeStreamRef.current = eventSource;

      // Track accumulated text outside of React state to avoid closure issues
      let accumulatedText = "";

      eventSource.onmessage = (event) => {
        console.log("Raw stream data received:", event.data);

        if (event.data === "[DONE]") {
          // Stream complete
          eventSource.close();
          activeStreamRef.current = null;
          setIsLoading(false);

          // Final update to remove streaming indicator
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === placeholderId ? { ...msg, isStreaming: false } : msg,
            ),
          );
          return;
        }

        try {
          // Handle cases where we might have truncated or malformed JSON
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (jsonError) {
            console.error(
              "JSON parse error:",
              jsonError,
              "Raw data:",
              event.data,
            );
            return; // Skip this chunk if it's not valid JSON
          }

          console.log("Parsed JSON data:", JSON.stringify(data));

          if (data.choices && data.choices[0] && data.choices[0].delta) {
            // Check specifically for content property
            const content = data.choices[0].delta.content || "";
            console.log("Extracted content:", content);
            
            // Only add to accumulated text if there's content
            if (content) {
              accumulatedText += content;

              // Only update UI state if there's content to add
              // Force a complete state replacement instead of incremental updates
              console.log("Before setMessages - placeholderId:", placeholderId);
              console.log("Before setMessages - accumulated text:", accumulatedText);
              
              setMessages((prev) => {
                // Check if we can find the placeholder message
                const foundMessage = prev.find(msg => msg.id === placeholderId);
                console.log("Found placeholder message:", foundMessage);
                
                if (!foundMessage) {
                  console.error("CRITICAL ERROR - Cannot find message with ID:", placeholderId);
                  console.log("Current messages:", prev);
                  // If we can't find the message, just return the original state
                  return prev;
                }
                
                const updated = prev.map((msg) =>
                  msg.id === placeholderId
                    ? { ...msg, text: accumulatedText }
                    : msg,
                );
                console.log("Updated messages:", updated);
              return updated;
            });
            }
          }
        } catch (err) {
          console.error("Error parsing streaming data:", err, event.data);
        }
      };

      eventSource.onerror = (error) => {
        console.error("Error with event source:", error);
        eventSource.close();
        activeStreamRef.current = null;
        setIsLoading(false);

        // Update with error message
        setMessages((prev) => {
          const placeholder = prev.find((msg) => msg.id === placeholderId);
          return prev.map((msg) =>
            msg.id === placeholderId
              ? {
                  ...msg,
                  text: placeholder.text || "Error with streaming response.",
                  isStreaming: false,
                }
              : msg,
          );
        });
      };
    } catch (error) {
      console.error("Failed to setup streaming:", error);
      setIsLoading(false);
      setMessages((prev) => {
        const withoutPlaceholder = prev.filter(
          (msg) => msg.id !== placeholderId,
        );
        return [
          ...withoutPlaceholder,
          {
            id: Date.now(),
            text: "Couldn't process streaming request.",
            sender: "ai",
          },
        ];
      });
    }
  };

  return (
    <div className="flex flex-col h-full p-4">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold">Chat Assistant</h2>
        <div className="flex items-center">
          <label htmlFor="streaming-toggle" className="mr-2 text-sm">
            Enable Streaming
          </label>
          <label className="relative inline-block w-12 h-6">
            <input
              id="streaming-toggle"
              type="checkbox"
              checked={streamingEnabled}
              onChange={() => setStreamingEnabled((prev) => !prev)}
              className="opacity-0 w-0 h-0"
            />
            <span
              className={`absolute cursor-pointer inset-0 rounded-full transition-colors duration-200 ease-in-out ${
                streamingEnabled ? "bg-blue-600" : "bg-gray-300"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-200 ease-in-out ${
                  streamingEnabled ? "transform translate-x-6" : ""
                }`}
              ></span>
            </span>
          </label>
        </div>
      </div>

      <div className="flex-grow overflow-y-auto mb-4 p-4 bg-white rounded-lg shadow">
        <div className="space-y-4">
          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              isStreaming={message.isStreaming}
            />
          ))}
          {isLoading && !messages.some((m) => m.isStreaming) && (
            <div className="flex justify-center items-center p-2">
              <div className="animate-pulse flex space-x-2">
                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-grow p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          disabled={isLoading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;

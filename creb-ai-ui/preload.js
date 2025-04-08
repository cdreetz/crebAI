// Secure bridge between renderer and main processes
const { contextBridge, ipcRenderer } = require("electron");

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld("electron", {
  sendMessage: (channel, data) => {
    // whitelist channels
    let validChannels = ["toMain", "api-request"];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  receive: (channel, func) => {
    let validChannels = ["fromMain", "api-response"];
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender`
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  },
});

contextBridge.exposeInMainWorld("api", {
  // Regular message sending (existing functionality)
  sendMessage: async (message) => {
    try {
      const result = await ipcRenderer.invoke("send-message", message);
      // Ensure we're returning a string if we get an object with task_id
      if (result && typeof result === "object") {
        if (result.task_id) {
          return {
            message: `Task ID: ${result.task_id}`,
            taskId: result.task_id,
          };
        }
        if (result.message) {
          return { message: result.message };
        }
        // If no message property, stringify the entire object
        return { message: JSON.stringify(result) };
      }
      // If result is a string, wrap it in an object with message property
      return { message: result };
    } catch (error) {
      console.error("Error sending message:", error);
      throw error;
    }
  },

  sendStreamingMessage: (message) => {
    try {
      const streamId = Date.now().toString();
      ipcRenderer.send("start-streaming", { streamId, message });

      const eventSource = {
        onmessage: null,
        onerror: null,
        close: function () {
          ipcRenderer.send("stop-streaming", { streamId });
          ipcRenderer.removeListener("streaming-event", eventListener);
        },
      };

      // Enhanced event listener with better debugging
      const eventListener = (event, data) => {
        console.log("Streaming event received:", data);

        if (data.streamId === streamId) {
          if (data.error && eventSource.onerror) {
            console.error("Streaming error:", data.error);
            eventSource.onerror(
              new ErrorEvent("error", { message: data.error }),
            );
          } else if (eventSource.onmessage) {
            // Make sure the data is properly passed to the message handler
            console.log("Passing streaming data to onmessage:", data.chunk);
            
            // Try to parse the data to make sure it's valid JSON before sending it to the renderer
            try {
              // For 'DONE' messages, pass as is
              if (data.chunk === '[DONE]') {
                eventSource.onmessage({ data: data.chunk });
                return;
              }
              
              // For JSON data, validate and modify if needed
              const jsonData = JSON.parse(data.chunk);
              
              // Create a fixed object format to ensure the data structure is correct
              const fixedData = JSON.stringify({
                ...jsonData,
                choices: jsonData.choices.map(choice => ({
                  ...choice,
                  delta: {
                    content: choice.delta.content || ''
                  }
                }))
              });
              
              console.log("Fixed streaming data:", fixedData);
              eventSource.onmessage({ data: fixedData });
            } catch (err) {
              console.error("Error preprocessing message data:", err);
              // Fall back to original behavior
              eventSource.onmessage({ data: data.chunk });
            }
          }

          if (data.done) {
            console.log("Streaming done, removing listener");
            ipcRenderer.removeListener("streaming-event", eventListener);
          }
        }
      };

      ipcRenderer.on("streaming-event", eventListener);
      return eventSource;
    } catch (error) {
      console.error("Error setting up streaming:", error);
      throw error;
    }
  },

  // Function to get status of a task
  getTaskStatus: async (taskId) => {
    try {
      return await ipcRenderer.invoke("get-task-status", taskId);
    } catch (error) {
      console.error("Error getting task status:", error);
      throw error;
    }
  },
});

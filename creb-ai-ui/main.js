// Electron main process file
const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const http = require("http");
const https = require("https");
const { URL } = require("url");

// API endpoint
const API_HOST = "127.0.0.1";
const API_PORT = 8020;
const API_PATH = "/api/v1/chat/chat";
const STREAMING_PATH = "/api/v1/chat/chat/stream";
const TASK_PATH = "/api/v1/tasks";

// Add this function near the top with your other constants
const POLL_INTERVAL = 1000; // 1 second

// Keep track of active streams
const activeStreams = new Map();

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.loadFile("index.html");

  // Open DevTools during development
  mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});

// Add this function to poll for results
async function pollForResult(taskId) {
  const options = {
    hostname: API_HOST,
    port: API_PORT,
    path: `${TASK_PATH}/${taskId}`,
    method: "GET",
    headers: {
      accept: "application/json",
    },
  };

  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let responseBody = "";

      res.on("data", (chunk) => {
        console.log("Received chunk:", chunk.toString());
        responseBody += chunk;
      });

      res.on("end", () => {
        try {
          const parsedData = JSON.parse(responseBody);
          console.log("Poll Response:", parsedData);
          resolve(parsedData);
        } catch (error) {
          reject(new Error("Failed to parse poll response"));
        }
      });
    });

    req.on("error", (error) => {
      console.error("Poll request error:", error);
      reject(new Error("Failed to poll for result"));
    });

    req.end();
  });
}

// Handle get-task-status requests from renderer process
ipcMain.handle("get-task-status", async (event, taskId) => {
  try {
    return await pollForResult(taskId);
  } catch (error) {
    console.error("Error getting task status:", error);
    throw error;
  }
});

// Handle streaming request - KEEP ONLY THIS VERSION
ipcMain.on("start-streaming", (event, { streamId, message }) => {
  try {
    // Convert frontend message format to API format
    const formattedMessages = [
      {
        content: "You are a helpful assistant.",
        role: "system",
      },
      ...message.map((msg) => ({
        content: msg.text,
        role: msg.sender === "ai" ? "assistant" : "user",
      })),
    ];

    // Prepare the request data as JSON
    const data = JSON.stringify({
      messages: formattedMessages,
      stream: true,
    });

    console.log(
      "Preparing streaming POST request to:",
      `http://${API_HOST}:${API_PORT}${STREAMING_PATH}`,
    );

    // Set up request options
    const options = {
      hostname: API_HOST,
      port: API_PORT,
      path: STREAMING_PATH,
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
      },
    };

    // Set up request
    const req = http.request(options, (res) => {
      console.log(`Streaming response status: ${res.statusCode}`);

      if (res.statusCode !== 200) {
        event.sender.send("streaming-event", {
          streamId,
          error: `HTTP error: ${res.statusCode}`,
          done: true,
        });
        return;
      }

      // Set up data handling
      let buffer = "";

      res.on("data", (chunk) => {
        const chunkStr = chunk.toString();
        console.log("Raw chunk received:", chunkStr);

        // Add the new chunk to our buffer
        buffer += chunkStr;

        // Process the buffer for complete SSE events
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep the last incomplete chunk

        // Process each complete event
        lines.forEach((line) => {
          if (!line.trim()) return; // Skip empty lines

          // Parse the SSE format - improved handling
          const dataLines = line.split("\n");
          const dataLine = dataLines.find((l) => l.startsWith("data:"));

          if (dataLine) {
            const eventData = dataLine.substring(5).trim(); // Remove "data: " prefix
            console.log("Parsed event data:", eventData);

            // Send raw data to renderer
            event.sender.send("streaming-event", {
              streamId,
              chunk: eventData,
              done: false,
            });
          }
        });
      });

      res.on("end", () => {
        console.log("Streaming response ended");
        // Send [DONE] event
        event.sender.send("streaming-event", {
          streamId,
          chunk: "[DONE]",
          done: true,
        });
        activeStreams.delete(streamId);
      });

      res.on("error", (error) => {
        console.error("Error in streaming response:", error);
        event.sender.send("streaming-event", {
          streamId,
          error: error.message,
          done: true,
        });
        activeStreams.delete(streamId);
      });
    });

    // Handle request errors
    req.on("error", (error) => {
      console.error("Streaming request error:", error);
      event.sender.send("streaming-event", {
        streamId,
        error: error.message,
        done: true,
      });
      activeStreams.delete(streamId);
    });

    // Store request for possible cancellation
    activeStreams.set(streamId, req);

    // Write the data and end the request
    req.write(data);
    req.end();
  } catch (error) {
    console.error("Error setting up streaming:", error);
    event.sender.send("streaming-event", {
      streamId,
      error: error.message,
      done: true,
    });
  }
});

// Handle stop streaming request
ipcMain.on("stop-streaming", (event, { streamId }) => {
  const req = activeStreams.get(streamId);
  if (req) {
    req.destroy();
    activeStreams.delete(streamId);
    console.log(`Streaming stopped for ${streamId}`);
  }
});

// Ensure all streams are aborted when the app is quitting
app.on("before-quit", () => {
  for (const req of activeStreams.values()) {
    req.destroy();
  }
  activeStreams.clear();
});

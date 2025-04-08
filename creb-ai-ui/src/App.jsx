import React from "react";
import { createRoot } from "react-dom/client";
import ChatWindow from "./components/ChatWindow";

const App = () => {
  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-xl font-bold">AI Chat Assistant</h1>
      </header>
      <main className="flex-grow overflow-hidden">
        <ChatWindow />
      </main>
      <footer className="bg-gray-200 text-center p-2 text-sm text-gray-600">
        AI Chat App v1.0
      </footer>
    </div>
  );
};

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);

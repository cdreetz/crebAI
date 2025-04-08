import React, { useEffect } from "react";
import { CopyToClipboard } from "react-copy-to-clipboard";
import Prism from "../utils/prism-setup";

// List of supported languages
const SUPPORTED_LANGUAGES = [
  "javascript",
  "jsx",
  "python",
  "java",
  "c",
  "cpp",
  "ruby",
  "rust",
  "go",
  "bash",
  "json",
  "yaml",
  "markdown",
  "sql",
  "plaintext",
];

const CodeBlock = ({ code, language }) => {
  const [copied, setCopied] = React.useState(false);
  const effectiveLanguage = SUPPORTED_LANGUAGES.includes(language)
    ? language
    : "plaintext";

  useEffect(() => {
    Prism.highlightAll();
  }, [code]);

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="rounded-lg !mt-0 !mb-0 bg-gray-800 p-3 overflow-x-auto">
        <code
          className={`language-${effectiveLanguage} text-xs font-mono leading-relaxed`}
        >
          {code}
        </code>
      </pre>
      <CopyToClipboard text={code} onCopy={handleCopy}>
        <button className="absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {copied ? "Copied!" : "Copy"}
        </button>
      </CopyToClipboard>
    </div>
  );
};

const Message = ({ message, isStreaming }) => {
  const isAi = message.sender === "ai";

  // Function to parse text and identify code blocks
  const parseContent = (text) => {
    const parts = [];
    let currentIndex = 0;
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;

    let match;
    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > currentIndex) {
        parts.push({
          type: "text",
          content: text.slice(currentIndex, match.index),
        });
      }

      // Add code block
      parts.push({
        type: "code",
        language: match[1] || "plaintext",
        content: match[2].trim(),
      });

      currentIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (currentIndex < text.length) {
      parts.push({
        type: "text",
        content: text.slice(currentIndex),
      });
    }

    return parts;
  };

  // Make sure message.text is not undefined before parsing
  const textContent = message.text || "";
  console.log("Message text content before parsing:", textContent);
  const content = parseContent(textContent);

  return (
    <div className={`flex ${isAi ? "justify-start" : "justify-end"} mb-4`}>
      <div
        className={`max-w-3/4 p-3 rounded-lg ${
          isAi ? "bg-gray-100 text-gray-800" : "bg-blue-600 text-white"
        } font-sans ${isStreaming ? "border-l-4 border-blue-600 animate-pulse" : ""}`}
      >
        {content.map((part, index) => (
          <div
            key={index}
            className={part.type === "code" ? "my-4 first:mt-0 last:mb-0" : ""}
          >
            {part.type === "code" ? (
              <CodeBlock code={part.content} language={part.language} />
            ) : (
              <p className="whitespace-pre-wrap text-base leading-relaxed">
                {part.content}
              </p>
            )}
          </div>
        ))}
        {isStreaming && (
          <div className="inline-block ml-1 animate-pulse">▌</div>
        )}
      </div>
    </div>
  );
};

export default Message;

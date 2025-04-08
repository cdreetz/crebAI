import { useState, useEffect } from 'react';

function Chat() {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [error, setError] = useState(null);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        try {
            const result = await window.api.sendMessage(inputMessage);
            console.log("Received result in Chat component:", result);
            
            // Create a new message object
            const newMessage = {
                id: Date.now(),
                text: inputMessage,
                sender: 'user'
            };

            // Create the response message
            const responseMessage = {
                id: Date.now() + 1,
                text: result.message || 'No response received',
                sender: 'assistant'
            };

            // Update messages with both the user message and response
            setMessages(prevMessages => [...prevMessages, newMessage, responseMessage]);
            setInputMessage(''); // Clear input
        } catch (err) {
            console.error("Error in handleSendMessage:", err);
            setError(err.message);
        }
    };

    return (
        <div className="flex flex-col h-screen">
            <div className="flex-1 overflow-y-auto p-4">
                {error && (
                    <div className="text-red-500 mb-4">
                        {error}
                    </div>
                )}
                
                {messages.map(message => (
                    <div 
                        key={message.id}
                        className={`mb-4 ${
                            message.sender === 'user' 
                                ? 'text-right' 
                                : 'text-left'
                        }`}
                    >
                        <div className={`inline-block p-2 rounded-lg ${
                            message.sender === 'user'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 text-black'
                        }`}>
                            {message.text}
                        </div>
                    </div>
                ))}
            </div>

            <form onSubmit={handleSendMessage} className="p-4 border-t">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        className="flex-1 p-2 border rounded"
                        placeholder="Type your message..."
                    />
                    <button 
                        type="submit"
                        className="px-4 py-2 bg-blue-500 text-white rounded"
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
}

export default Chat; 
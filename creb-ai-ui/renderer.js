// Instead of directly using sendMessage, use:
window.electron.sendMessage('channel-name', data);

// And to receive messages:
window.electron.receive('channel-name', (data) => {
    console.log('Received:', data);
});

// Remove the previous electron.sendMessage code
// Instead use the api.sendMessage function like this:
async function sendMessage(message) {
    try {
        const response = await window.api.sendMessage(message);
        return response;
    } catch (error) {
        console.error('Failed to send message:', error);
        throw error;
    }
} 
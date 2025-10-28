import { useState } from 'react';

// Main App component
export default function App() {
  // State for the current value in the input bar
  const [inputValue, setInputValue] = useState('');
  // State to hold all chat messages
  const [messages, setMessages] = useState([
    { id: 1, sender: 'api', text: 'Hello! How can I help you today?' }
  ]);
  // State to track if the API is "thinking"
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handles the submission of the chat form
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    const userMessage = inputValue.trim();

    if (!userMessage) {
      return; // Don't send empty messages
    }

    // Add user's message to the chat
    setMessages(prev => [
      ...prev,
      { id: Date.now(), sender: 'user', text: userMessage }
    ]);

    // Clear the input bar
    setInputValue('');
    // Set loading state to true
    setIsLoading(true);

    // --- YOUR API CALL GOES HERE ---
    // Simulate an API call with a delay
    // Replace this with your actual `fetch` or `axios` call
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // This is your mock API response
      const apiResponseText = `You said: "${userMessage}". This is a placeholder response.`;

      // Add API's response to the chat
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, sender: 'api', text: apiResponseText }
      ]);

    } catch (error) {
      console.error("Error fetching API response:", error);
      // Show an error message to the user
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, sender: 'api', text: 'Sorry, I ran into an error. Please try again.' }
      ]);
    } finally {
      // Set loading state to false
      setIsLoading(false);
    }
    // --- END OF API CALL SECTION ---
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <h1 className="text-xl font-semibold text-gray-800 text-center">Chat with API</h1>
      </header>

      {/* Message Display Area */}
      <div className="flex-grow p-4 space-y-4 overflow-y-auto">
        {messages.map(message => (
          <ChatMessage key={message.id} sender={message.sender} text={message.text} />
        ))}
        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-700 p-3 rounded-lg max-w-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input Bar */}
      <footer className="bg-white border-t border-gray-200 p-4 shadow-inner">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="flex-grow p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading} // Disable input while loading
          />
          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400"
            disabled={isLoading} // Disable button while loading
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}

/**
 * Component to render a single chat message
 * @param {object} props
 * @param {'user' | 'api'} props.sender - The sender of the message
 * @param {string} props.text - The content of the message
 */
function ChatMessage({ sender, text }) {
  const isUser = sender === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`p-3 rounded-lg max-w-lg shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        <p>{text}</p>
      </div>
    </div>
  );
}

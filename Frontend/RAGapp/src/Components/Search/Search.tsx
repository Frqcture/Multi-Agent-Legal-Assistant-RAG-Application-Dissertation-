import React from 'react';
import styles from './Search.module.css';
import { BiArrowToRight } from "react-icons/bi";

//Define the structure of a message
interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
}

// Define the shape of your request body
interface AskRequest {
    question: string;
}

// Define the shape of the expected response (optional but recommended)
interface AskResponse {
    answer: string; // Adjust based on your actual API response
}

async function askQuestion(question: string): Promise<Message | void> {
    const url = 'http://127.0.0.1:8000/ask';

    const payload: AskRequest = { question };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(`Error! status: ${response.status}`);
        }

        const result = (await response.json()) as AskResponse;

        const botMessage: Message = {
            id: Date.now(),
            text: result.answer,
            sender: 'bot'
        };

        console.log('Response:', result);
        return botMessage;
    } catch (error) {
        console.error('Failed to fetch:', error);
    }
}

const Search: React.FC = () => {
    const [inputValue, setInputValue] = React.useState<string>("");
    const [messages, setMessages] = React.useState<Message[]>([]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(event.target.value);
    }

    const handleSend = async () => {

        const userMessage: Message = {
            id: Date.now(),
            text: inputValue,
            sender: 'user'
        }

        console.log("Question submitted:", inputValue);

        setMessages(prevMessages => [...prevMessages, userMessage]); //Add user message to end of the chat

        setInputValue(""); // Clear input after sending

        const botMessage = await askQuestion(inputValue);
        if (botMessage) {
            setMessages(prevMessages => [...prevMessages, botMessage]); //Add bot response to end of the chat
        }
    }

    const handleEnterKey = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend();
        }
    }

    return (
        <div className={styles.pageContainer}>
            <div className={styles.contentWrapper}>

                {/* Title Section */}
                {messages.length === 0 && ( // Show title only if no messages yet
                    <div className={styles.headerSection}>
                        <h1 className={styles.mainTitle}>Ask me a question!</h1>
                    </div>
                )}

                {/* Messages History Display Area */}
                <div className={styles.messageHistory}>
                  {messages.map((message) => ( //For each message in messages array
                    <div key={message.id} className={`${styles.messageRow} ${styles[message.sender]}`}>
                        <div className={styles.messageBubble}>
                          {message.text}
                        </div>
                    </div>
                  ))}
                </div>

                {/* The Input Box Section */}
                <div className={styles.searchContainer}>

                    {/* The Text Input */}
                    <input
                        type="text"
                        className={styles.searchInput}
                        placeholder="Ask your question here..."
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleEnterKey}
                    />

                    {/* Right Actions */}
                    <div className={styles.rightActions}>
                        <div className={styles.iconButton} role="button" aria-label="Submit Question" onClick={handleSend}>
                            <BiArrowToRight />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Search;
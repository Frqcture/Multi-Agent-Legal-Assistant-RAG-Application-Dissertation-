import React from 'react';
import styles from './Search.module.css';
import { BiArrowToRight } from "react-icons/bi";

// Define the shape of your request body
interface AskRequest {
    question: string;
}

// Define the shape of the expected response (optional but recommended)
interface AskResponse {
    answer: string; // Adjust based on your actual API response
}

async function askQuestion(question: string): Promise<AskResponse | void> {
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
        console.log('Response:', result);
        return result;
    } catch (error) {
        console.error('Failed to fetch:', error);
    }
}

const Search: React.FC = () => {
    const [inputValue, setInputValue] = React.useState<string>("");

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(event.target.value);
    }

    const handleSend = () => {
        console.log("Question submitted:", inputValue);

        //Logic to handle the question submission
        askQuestion(inputValue);


        setInputValue(""); // Clear input after sending
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
                <div className={styles.headerSection}>
                    <h1 className={styles.mainTitle}>Ask me a question!</h1>
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
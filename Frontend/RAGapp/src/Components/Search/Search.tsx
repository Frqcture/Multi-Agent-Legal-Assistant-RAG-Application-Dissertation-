import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Search.module.css';
import { BiArrowToRight, BiBook, BiLibrary } from "react-icons/bi";
import { CiLogout } from "react-icons/ci";
import { FiX, FiTrash2 } from 'react-icons/fi';

// Define the structure of a message
interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
}

interface AskRequest {
    question: string;
}

interface AskResponse {
    answer: string;
}

// --- API Helpers ---
const BASE_URL = 'http://0.0.0.0:8000';

async function logoutUser() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// Function to ask a question to the backend API
async function askQuestion(question: string): Promise<Message | void> {
    const token = localStorage.getItem('access_token'); // Retrieve stored token

    const url = `${BASE_URL}/ask`;
    const payload: AskRequest = { question };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload),
        });

        if (response.status === 401) {
            // Handle expired token or unlogged user
            window.location.href = '/login';
            return;
        }

        if (!response.ok) throw new Error(`Error! status: ${response.status}`);

        const result = (await response.json()) as AskResponse;
        return {
            id: Date.now(),
            text: result.answer,
            sender: 'bot'
        };
    } catch (error) {
        console.error('Failed to fetch:', error);
    }
}

// Function to handle the PDF upload
async function uploadPDF(file: File): Promise<{ message: string; status: string } | null> {
    const token = localStorage.getItem('access_token'); // Retrieve stored token

    const url = `${BASE_URL}/upload`;
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`, // Send token to backend
            },
            body: formData, // No headers needed, browser sets boundary
            
        });

        if (!response.ok) throw new Error('Upload failed');
        return await response.json();
    } catch (error) {
        console.error('Upload error:', error);
        return null;
    }
}

const Search: React.FC = () => {
    const navigate = useNavigate(); // Initialize navigate

    const [inputValue, setInputValue] = useState<string>("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isIngesting, setIsIngesting] = useState<boolean>(false);

    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [userFiles, setUserFiles] = useState<string[]>([]);
    
    // Ref to trigger the hidden file input
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Security Check: Redirect if no token is found
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            navigate('/login'); // Kick user back to login
        }
    }, [navigate]);

    const fetchFiles = async () => {
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${BASE_URL}/files`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setUserFiles(data.files);
            }
        } catch (error) {
            console.error("Failed to fetch files:", error);
        }
    };

    const handleDeleteFile = async (filename: string) => {
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                // Refresh list after deletion
                setUserFiles(prev => prev.filter(f => f !== filename));
            }
        } catch (error) {
            console.error("Delete failed:", error);
        }
    };

    const handleOpenLibrary = () => {
        setIsModalOpen(true);
        fetchFiles();
    };

    // --- Input Handlers ---
    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(event.target.value);
    }

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMessage: Message = {
            id: Date.now(),
            text: inputValue,
            sender: 'user'
        }

        setMessages(prev => [...prev, userMessage]);
        setInputValue("");

        const botMessage = await askQuestion(inputValue);
        if (botMessage) {
            setMessages(prev => [...prev, botMessage]);
        }
    }

    // --- File Upload Handlers ---

    const handleBookClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsIngesting(true);
        
        // Add a system message to the chat
        const systemMsg: Message = {
            id: Date.now(),
            text: `Uploading and indexing "${file.name}"...`,
            sender: 'bot'
        };
        setMessages(prev => [...prev, systemMsg]);

        const result = await uploadPDF(file);

        if (result) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                text: `Success: ${file.name} is now in the knowledge base.`,
                sender: 'bot'
            }]);
        } else {
            setMessages(prev => [...prev, {
                id: Date.now(),
                text: `Failed to upload ${file.name}. Please try again.`,
                sender: 'bot'
            }]);
        }

        setIsIngesting(false);
        if (fileInputRef.current) fileInputRef.current.value = ''; // Reset input
    };

    // Handle Enter key press in input
    const handleEnterKey = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') handleSend();
    }

    return (
        <div className={styles.pageContainer}>
            <div className={styles.navbar}>
                <button className={styles.navButton} onClick={handleOpenLibrary}>
                  <BiLibrary /> Library
                </button>
                <button className={styles.navButton} onClick={logoutUser}>
                    <CiLogout /> Logout  
                </button>
            </div>
            <div className={styles.contentWrapper}>

                {messages.length === 0 && (
                    <div className={styles.headerSection}>
                        <h1 className={styles.mainTitle}>Ask me a question!</h1>
                    </div>
                )}

                <div className={styles.messageHistory}>
                  {messages.map((message) => (
                    <div key={message.id} className={`${styles.messageRow} ${styles[message.sender]}`}>
                        <div className={styles.messageBubble}>
                          {message.text}
                        </div>
                    </div>
                  ))}
                </div>

                <div className={styles.searchContainer}>
                    {/* Hidden File Input */}
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        accept=".pdf"
                        onChange={handleFileChange}
                    />

                    <input
                        type="text"
                        className={styles.searchInput}
                        placeholder={isIngesting ? "Processing document..." : "Ask your question here..."}
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleEnterKey}
                        disabled={isIngesting}
                    />

                    <div className={styles.rightActions}>
                        <div 
                            className={styles.iconButton} 
                            role="button" 
                            aria-label="Upload File" 
                            onClick={handleBookClick}
                        >
                            <BiBook />
                        </div>
                        <div 
                            className={styles.iconButton} 
                            role="button" 
                            aria-label="Submit Question" 
                            onClick={handleSend}
                        >
                            <BiArrowToRight />
                        </div>
                    </div>
                </div>
            </div>

            {/* --- Library Modal Popup --- */}
            {isModalOpen && (
                <div className={styles.modalOverlay} onClick={() => setIsModalOpen(false)}>
                    <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h2>Your Uploaded Documents</h2>
                            <FiX className={styles.closeIcon} onClick={() => setIsModalOpen(false)} />
                        </div>
                        <div className={styles.fileList}>
                            {userFiles.length === 0 ? (
                                <p className={styles.emptyMsg}>No documents uploaded yet.</p>
                            ) : (
                                userFiles.map((filename) => (
                                    <div key={filename} className={styles.fileItem}>
                                        <span className={styles.fileName}>{filename}</span>
                                        <FiTrash2 
                                            className={styles.deleteIcon} 
                                            onClick={() => handleDeleteFile(filename)} 
                                        />
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Search;
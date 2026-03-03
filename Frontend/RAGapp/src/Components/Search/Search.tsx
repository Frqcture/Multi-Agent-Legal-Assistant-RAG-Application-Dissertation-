import React, { useRef, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Search.module.css';
import { BiArrowToRight, BiBook, BiLibrary } from "react-icons/bi";
import { BiBrain, BiSearch, BiMessageDetail, BiWorld, BiFile } from "react-icons/bi";
import { CiLogout } from "react-icons/ci";
import { FiX, FiTrash2, FiEye, FiEyeOff, FiExternalLink } from 'react-icons/fi';
import ProactiveDashboard from './ProactiveDashboard';

// Define the structure of a message
interface AgentStep {
    agent: string;
    message: string;
    timestamp: string;
    tool_calls: Array<{ tool: string; args: Record<string, unknown> }>;
    tool_results: Array<Record<string, unknown>>;
}

interface WebSource {
    title: string;
    url: string;
    snippet: string;
}

interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
    steps?: AgentStep[];
    web_searched?: boolean;
    web_sources?: WebSource[];
}

interface AskRequest {
    question: string;
}

interface AskResponse {
    answer: string;
    steps: AgentStep[];
    status: string;
    web_searched?: boolean;
    web_sources?: WebSource[];
}

// --- API Helpers ---
const BASE_URL = import.meta.env.VITE_API_BASE_URL;
const CSRF_COOKIE_NAME = 'csrf_token';

function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop()?.split(';').shift() ?? null;
    }
    return null;
}

async function logoutUser() {
    try {
            const csrfToken = getCookie(CSRF_COOKIE_NAME);
      const response = await fetch(`${BASE_URL}/logout`, {
        method: 'POST',
                headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : undefined,
        credentials: 'include',
      });

      if(!response.ok) {
        console.error("Logout failed on server, but clearing client session.");
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear client-side breadcrumbs from old auth method
      localStorage.removeItem('access_token');

      // Redirect to login page
      window.location.href = '/login';
    }
}

// Function to ask a question to the backend API
async function askQuestion(question: string): Promise<Message | void> {

    const url = `${BASE_URL}/ask`;
    const payload: AskRequest = { question };

    try {
        const csrfToken = getCookie(CSRF_COOKIE_NAME);
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
            },
            credentials: 'include',
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
            sender: 'bot',
            steps: result.steps,
            web_searched: result.web_searched ?? false,
            web_sources: result.web_sources ?? [],
        };
    } catch (error) {
        console.error('Failed to fetch:', error);
    }
}

// Function to handle the PDF upload
async function uploadPDFs(files: FileList): Promise<{ message: string; status: string } | null> {

    const url = `${BASE_URL}/upload`;
    const formData = new FormData();

    Array.from(files).forEach(file => {
      formData.append('files', file);
    })

    try {
        const csrfToken = getCookie(CSRF_COOKIE_NAME);
        const response = await fetch(url, {
            method: 'POST',
            credentials: 'include',
            headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : undefined,
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
    const [showSteps, setShowSteps] = useState<boolean>(true);

    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [userFiles, setUserFiles] = useState<string[]>([]);
    const [lastAskedQuery, setLastAskedQuery] = useState<string>("");
    const [jurisdiction, setJurisdiction] = useState<{ name: string; confidence: string; detected_from: string } | null>(null);
    
    // Ref to trigger the hidden file input
    const fileInputRef = useRef<HTMLInputElement>(null);
    const contentWrapperRef = useRef<HTMLDivElement>(null);
    const [autoCollapsed, setAutoCollapsed] = useState(false);
    const lockRef = useRef(false);

    // Route all wheel events to the content wrapper
    useEffect(() => {
        const handleWheel = (event: WheelEvent) => {
            const container = contentWrapperRef.current;
            if (!container) return;
            const maxScrollTop = container.scrollHeight - container.clientHeight;
            if (maxScrollTop <= 0) return;
            container.scrollTop = Math.min(
                maxScrollTop,
                Math.max(0, container.scrollTop + event.deltaY)
            );
            event.preventDefault();
        };

        window.addEventListener('wheel', handleWheel, { passive: false });
        return () => window.removeEventListener('wheel', handleWheel);
    }, []);

    // Auto-collapse insights only when there's actually enough content
    // to need scrolling, and the user has scrolled down.
    useEffect(() => {
        const wrapper = contentWrapperRef.current;
        if (!wrapper) return;

        const onScroll = () => {
            if (lockRef.current) return;

            const scrollTop = wrapper.scrollTop;
            const hasOverflow = wrapper.scrollHeight > wrapper.clientHeight + 100;

            setAutoCollapsed((prev) => {
                if (!prev && hasOverflow && scrollTop > 80) {
                    lockRef.current = true;
                    setTimeout(() => { lockRef.current = false; }, 500);
                    return true;
                }
                if (prev && scrollTop < 5) {
                    lockRef.current = true;
                    setTimeout(() => { lockRef.current = false; }, 500);
                    return false;
                }
                return prev;
            });
        };

        wrapper.addEventListener('scroll', onScroll, { passive: true });
        return () => wrapper.removeEventListener('scroll', onScroll);
    }, []);

    const handleExpandInsights = () => {
        const wrapper = contentWrapperRef.current;
        if (!wrapper) return;
        lockRef.current = true;
        setAutoCollapsed(false);
        wrapper.scrollTo({ top: 0, behavior: 'smooth' });
        setTimeout(() => { lockRef.current = false; }, 600);
    };

    const handleJurisdictionChange = useCallback((j: { name: string; confidence: string; detected_from: string } | null) => {
        setJurisdiction(j);
    }, []);

    const fetchFiles = async () => {
        try {
            const response = await fetch(`${BASE_URL}/files`, {
                credentials: 'include'
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
        try {
            const csrfToken = getCookie(CSRF_COOKIE_NAME);
            const response = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
                headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : undefined,
                credentials: 'include'
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
        setLastAskedQuery(inputValue);
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
        const files = event.target.files;
        
        if (!files || files.length === 0) return;

        setIsIngesting(true);
        
        // Add a system message to the chat
        const systemMsg: Message = {
            id: Date.now(),
            text: `Uploading and indexing "${files.length} documents"...`,
            sender: 'bot'
        };
        setMessages(prev => [...prev, systemMsg]);

        const result = await uploadPDFs(files);

        if (result) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                text: `Success: ${files.length} documents are now in the knowledge base.`,
                sender: 'bot'
            }]);
        } else {
            setMessages(prev => [...prev, {
                id: Date.now(),
                text: `Failed to upload. Please try again.`,
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
            {/* Jurisdiction badge — top left */}
            {jurisdiction && jurisdiction.name && jurisdiction.name !== 'Unknown' && (
                <div className={styles.jurisdictionBadge} title={jurisdiction.detected_from}>
                    <span className={styles.jurisdictionLabel}>Jurisdiction:</span>{' '}
                    <span className={styles.jurisdictionName}>{jurisdiction.name}</span>
                    <span className={`${styles.jurisdictionConf} ${styles[`conf_${jurisdiction.confidence}`]}`}>
                        {jurisdiction.confidence}
                    </span>
                </div>
            )}
            <div className={styles.navbar}>
                <button
                    className={`${styles.navButton} ${showSteps ? styles.navButtonActive : ''}`}
                    onClick={() => setShowSteps(!showSteps)}
                >
                  {showSteps ? <FiEye /> : <FiEyeOff />} {showSteps ? 'Steps Visible' : 'Steps Hidden'}
                </button>
                <button className={styles.navButton} onClick={handleOpenLibrary}>
                  <BiLibrary /> Library
                </button>
                <button className={styles.navButton} onClick={logoutUser}>
                    <CiLogout /> Logout  
                </button>
            </div>
            <div className={styles.contentWrapper} ref={contentWrapperRef}>
                {/* {messages.length === 0 && (
                    <div className={styles.headerSection}>
                        <h1 className={styles.mainTitle}>Legal Assistant</h1>
                        <p className={styles.subtitle}>Ask me a legal question</p>
                    </div>
                )} */}

                <div className={styles.insightsSection}>
                    <ProactiveDashboard
                        baseUrl={BASE_URL}
                        latestQuery={lastAskedQuery}
                        autoCollapsed={autoCollapsed}
                        onExpand={handleExpandInsights}
                        onJurisdictionChange={handleJurisdictionChange}
                    />
                </div>

                <div className={styles.messageHistory}>
                  {messages.map((message) => (
                    <div key={message.id} className={`${styles.messageRow} ${styles[message.sender]}`}>
                        <div className={styles.messageBubble}>
                          {message.text}
                          {/* Web search indicator */}
                          {message.web_searched && (
                            <div className={styles.webSearchBanner}>
                                <div className={styles.webSearchHeader}>
                                    <BiWorld className={styles.webSearchIcon} />
                                    <span>Answer sourced from web search — your documents did not contain this information</span>
                                </div>
                                {message.web_sources && message.web_sources.length > 0 && (
                                    <ul className={styles.webSourceList}>
                                        {message.web_sources.map((src, i) => (
                                            <li key={i} className={styles.webSourceItem}>
                                                <a
                                                    href={src.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className={styles.webSourceLink}
                                                >
                                                    {src.title || src.url}
                                                    <FiExternalLink className={styles.webSourceExtIcon} />
                                                </a>
                                                {src.snippet && (
                                                    <span className={styles.webSourceSnippet}>{src.snippet}</span>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                          )}
                          {/* Inline agent steps */}
                          {showSteps && message.steps && message.steps.length > 0 && (
                            <div className={styles.stepsContainer}>
                              {message.steps.map((step, idx) => {
                                const iconMap: Record<string, React.ReactNode> = {
                                    planner: <BiBrain />,
                                    retriever: <BiSearch />,
                                    responder: <BiMessageDetail />,
                                    drafter: <BiFile />,
                                };
                                return (
                                  <div key={idx} className={styles.stepItem}>
                                    <div className={`${styles.stepIcon} ${styles[`step_${step.agent}`]}`}>
                                      {iconMap[step.agent] ?? <BiSearch />}
                                    </div>
                                    <div className={styles.stepBody}>
                                      <span className={styles.stepAgent}>{step.agent}</span>
                                      <span className={styles.stepMessage}>{step.message}</span>
                                      {step.tool_calls.length > 0 && (
                                        <div className={styles.stepTools}>
                                          {step.tool_calls.map((tc, i) => (
                                            <span key={i} className={styles.toolCall}>
                                              → {tc.tool}({Object.keys(tc.args).join(', ')})
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
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
                        multiple
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
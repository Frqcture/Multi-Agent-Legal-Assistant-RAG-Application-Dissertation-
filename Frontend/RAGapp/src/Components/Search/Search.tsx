import React from 'react';
import styles from './Search.module.css';
import { BiArrowToRight } from "react-icons/bi";


const Search: React.FC = () => {
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
                    />

                    {/* Right Actions */}
                    <div className={styles.rightActions}>
                        <div className={styles.iconButton} role="button" aria-label="Submit Question">
                            <BiArrowToRight />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Search;
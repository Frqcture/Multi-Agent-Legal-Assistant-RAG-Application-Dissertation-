import React from 'react';
import styles from './Search.module.css';
import { BiArrowToRight } from "react-icons/bi";

// Simple SVG components for the UI icons
const PlusIcon = () => (
  <svg className={styles.svgIcon} viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
);

const ToolsIcon = () => (
    <svg className={styles.svgIconSmall} viewBox="0 0 24 24"><path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z"/></svg>
);

const MicIcon = () => (
  <svg className={styles.svgIcon} viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
);

const ChevronDownIcon = () => (
    <svg className={styles.svgIconSmall} viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
);


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
            placeholder="Ask Gemini 3" 
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
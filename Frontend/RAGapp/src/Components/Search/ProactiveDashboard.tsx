import React, { useState, useEffect, useCallback } from 'react';
import styles from './ProactiveDashboard.module.css';
import {
    BiTargetLock,
    BiBookBookmark,
    BiListCheck,
    BiError,
    BiRefresh,
    BiChevronDown,
    BiChevronUp,
} from 'react-icons/bi';

// ── Types ──────────────────────────────────────────────────────────────────

interface NextAction {
    action: string;
    priority: 'high' | 'medium' | 'low';
    reason: string;
}

interface RelatedStatute {
    statute: string;
    relevance: string;
    jurisdiction: string;
}

interface ChecklistItem {
    item: string;
    completed: boolean;
    category: string;
}

interface InfoGap {
    field: string;
    severity: 'high' | 'medium' | 'low';
    suggestion: string;
}

interface ProactiveInsights {
    next_actions: NextAction[];
    related_statutes: RelatedStatute[];
    checklist: ChecklistItem[];
    info_gaps: InfoGap[];
}

interface ProactiveDashboardProps {
    baseUrl: string;
    latestQuery?: string;
    autoCollapsed?: boolean;
    onExpand?: () => void;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const CHECKLIST_STORAGE_KEY = 'proactive_checklist';
const CSRF_COOKIE_NAME = 'csrf_token';

function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop()?.split(';').shift() ?? null;
    }
    return null;
}

function loadSavedChecklist(): Record<string, boolean> {
    try {
        const raw = localStorage.getItem(CHECKLIST_STORAGE_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch {
        return {};
    }
}

function saveChecklist(items: ChecklistItem[]) {
    const map: Record<string, boolean> = {};
    items.forEach((c) => { map[c.item] = c.completed; });
    localStorage.setItem(CHECKLIST_STORAGE_KEY, JSON.stringify(map));
}

function mergeChecklist(fresh: ChecklistItem[]): ChecklistItem[] {
    const saved = loadSavedChecklist();
    return fresh.map((c) => ({
        ...c,
        completed: saved[c.item] !== undefined ? saved[c.item] : c.completed,
    }));
}

const priorityBadge: Record<string, string> = {
    high: styles.badgeHigh,
    medium: styles.badgeMedium,
    low: styles.badgeLow,
};

// ── Sub‑components ─────────────────────────────────────────────────────────

const NextActionsCard: React.FC<{ items: NextAction[]; autoCollapsed?: boolean; onExpand?: () => void }> = ({ items, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };
    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiTargetLock className={styles.cardIcon} />
                    <span>Next Best Actions</span>
                    <span className={styles.count}>{items.length}</span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {items.map((a, i) => (
                        <div key={i} className={styles.actionRow}>
                            <span className={`${styles.badge} ${priorityBadge[a.priority] ?? styles.badgeMedium}`}>
                                {a.priority}
                            </span>
                            <div className={styles.actionText}>
                                <span className={styles.actionLabel}>{a.action}</span>
                                <span className={styles.actionReason}>{a.reason}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const StatutesCard: React.FC<{ items: RelatedStatute[]; autoCollapsed?: boolean; onExpand?: () => void }> = ({ items, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };
    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiBookBookmark className={styles.cardIcon} />
                    <span>Related Statutes</span>
                    <span className={styles.count}>{items.length}</span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {items.length === 0 ? (
                        <p className={styles.emptyText}>Upload documents to see related statutes.</p>
                    ) : (
                        items.map((s, i) => (
                            <div key={i} className={styles.statuteRow}>
                                <span className={styles.statuteName}>{s.statute}</span>
                                <span className={styles.statuteRelevance}>{s.relevance}</span>
                                <span className={styles.statuteJurisdiction}>{s.jurisdiction}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

const ChecklistCard: React.FC<{
    items: ChecklistItem[];
    onToggle: (idx: number) => void;
    autoCollapsed?: boolean;
    onExpand?: () => void;
}> = ({ items, onToggle, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };
    const completed = items.filter((c) => c.completed).length;
    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiListCheck className={styles.cardIcon} />
                    <span>Case Checklist</span>
                    <span className={styles.count}>
                        {completed}/{items.length}
                    </span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {items.map((c, i) => (
                        <label key={i} className={styles.checkRow}>
                            <input
                                type="checkbox"
                                checked={c.completed}
                                onChange={() => onToggle(i)}
                                className={styles.checkbox}
                            />
                            <span className={c.completed ? styles.checkedText : ''}>
                                {c.item}
                            </span>
                            <span className={styles.categoryTag}>{c.category}</span>
                        </label>
                    ))}
                </div>
            </div>
        </div>
    );
};

const InfoGapsCard: React.FC<{ items: InfoGap[]; autoCollapsed?: boolean; onExpand?: () => void }> = ({ items, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };
    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiError className={styles.cardIcon} />
                    <span>Information Gaps</span>
                    <span className={styles.count}>{items.length}</span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {items.map((g, i) => (
                        <div key={i} className={styles.gapRow}>
                            <span className={`${styles.badge} ${priorityBadge[g.severity] ?? styles.badgeMedium}`}>
                                {g.severity}
                            </span>
                            <div className={styles.gapText}>
                                <span className={styles.gapField}>{g.field}</span>
                                <span className={styles.gapSuggestion}>{g.suggestion}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// ── Main Dashboard ─────────────────────────────────────────────────────────

const ProactiveDashboard: React.FC<ProactiveDashboardProps> = ({
    baseUrl,
    latestQuery = '',
    autoCollapsed = false,
    onExpand,
}) => {
    const [insights, setInsights] = useState<ProactiveInsights | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [checklist, setChecklist] = useState<ChecklistItem[]>([]);

    const fetchInsights = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const csrfToken = getCookie(CSRF_COOKIE_NAME);
            const headers: Record<string, string> = { 'Content-Type': 'application/json' };
            if (csrfToken) {
                headers['X-CSRF-Token'] = csrfToken;
            }
            const res = await fetch(`${baseUrl}/proactive-insights`, {
                method: 'POST',
                headers,
                credentials: 'include',
                body: JSON.stringify({ query: latestQuery }),
            });

            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            if (!res.ok) throw new Error(`Server error ${res.status}`);

            const data: ProactiveInsights = await res.json();
            setInsights(data);
            setChecklist(mergeChecklist(data.checklist));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load insights');
        } finally {
            setLoading(false);
        }
    }, [baseUrl, latestQuery]);

    // Fetch on mount and when the query changes meaningfully
    useEffect(() => {
        fetchInsights();
    }, [fetchInsights]);

    const handleChecklistToggle = (idx: number) => {
        setChecklist((prev) => {
            const updated = prev.map((item, i) =>
                i === idx ? { ...item, completed: !item.completed } : item
            );
            saveChecklist(updated);
            return updated;
        });
    };

    // ── Render ─────────────────────────────────────────────────────────────

    return (
        <div className={styles.dashboard}>
            <div className={styles.dashboardHeader}>
                <h2 className={styles.dashboardTitle}>Case Insights</h2>
                <button
                    className={styles.refreshBtn}
                    onClick={fetchInsights}
                    disabled={loading}
                    title="Refresh insights"
                >
                    <BiRefresh className={loading ? styles.spinning : ''} />
                </button>
            </div>

            {error && <div className={styles.errorBar}>{error}</div>}

            {loading && !insights && (
                <div className={styles.loadingState}>
                    <div className={styles.shimmer} />
                    <div className={styles.shimmer} />
                    <div className={styles.shimmer} />
                    <div className={styles.shimmer} />
                </div>
            )}

            {insights && (
                <div className={styles.grid}>
                    <NextActionsCard items={insights.next_actions} autoCollapsed={autoCollapsed} onExpand={onExpand} />
                    <StatutesCard items={insights.related_statutes} autoCollapsed={autoCollapsed} onExpand={onExpand} />
                    <ChecklistCard items={checklist} onToggle={handleChecklistToggle} autoCollapsed={autoCollapsed} onExpand={onExpand} />
                    <InfoGapsCard items={insights.info_gaps} autoCollapsed={autoCollapsed} onExpand={onExpand} />
                </div>
            )}
        </div>
    );
};

export default ProactiveDashboard;

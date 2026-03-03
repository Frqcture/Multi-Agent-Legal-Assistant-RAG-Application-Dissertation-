import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
import styles from './ProactiveDashboard.module.css';
import {
    BiTargetLock,
    BiBookBookmark,
    BiListCheck,
    BiError,
    BiRefresh,
    BiChevronDown,
    BiChevronUp,
    BiInfoCircle,
    BiCalendarEvent,
    BiShieldQuarter,
} from 'react-icons/bi';

// ── Types ──────────────────────────────────────────────────────────────────

interface NextAction {
    action: string;
    priority: 'high' | 'medium' | 'low';
    reason: string;
    shown_because?: string;
}

interface RelatedStatute {
    statute: string;
    relevance: string;
    jurisdiction: string;
    shown_because?: string;
}

interface ChecklistItem {
    item: string;
    completed: boolean;
    category: string;
    shown_because?: string;
}

interface InfoGap {
    field: string;
    severity: 'high' | 'medium' | 'low';
    suggestion: string;
    shown_because?: string;
}

interface Deadline {
    title: string;
    date: string;
    source: string;
    urgency: 'high' | 'medium' | 'low';
    description: string;
    shown_because?: string;
}

interface Conflict {
    party_name: string;
    documents: string[];
    conflict_type: string;
    severity: 'high' | 'medium' | 'low';
    description: string;
    shown_because?: string;
}

interface Jurisdiction {
    name: string;
    confidence: 'high' | 'medium' | 'low';
    detected_from: string;
}

interface ProactiveInsights {
    next_actions: NextAction[];
    related_statutes: RelatedStatute[];
    checklist: ChecklistItem[];
    info_gaps: InfoGap[];
    deadlines: Deadline[];
    conflicts: Conflict[];
    section_relevance: Record<string, number>;
    visible_sections: string[];
    jurisdiction: Jurisdiction;
}

interface ProactiveDashboardProps {
    baseUrl: string;
    latestQuery?: string;
    autoCollapsed?: boolean;
    onExpand?: () => void;
    onJurisdictionChange?: (jurisdiction: Jurisdiction | null) => void;
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

// ── Tooltip helper ────────────────────────────────────────────────────────

const InfoTip: React.FC<{ text?: string }> = ({ text }) => {
    const [visible, setVisible] = useState(false);
    const [coords, setCoords] = useState({ top: 0, left: 0 });
    const iconRef = useRef<HTMLSpanElement>(null);

    if (!text) return null;

    const handleMouseEnter = () => {
        if (iconRef.current) {
            const rect = iconRef.current.getBoundingClientRect();
            setCoords({ top: rect.top, left: rect.left + rect.width / 2 });
            setVisible(true);
        }
    };

    return (
        <>
            <span
                ref={iconRef}
                className={styles.infoTip}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={() => setVisible(false)}
            >
                <BiInfoCircle />
            </span>
            {visible && ReactDOM.createPortal(
                <div
                    className={styles.infoTipPortal}
                    style={{ top: coords.top, left: coords.left }}
                >
                    {text}
                </div>,
                document.body
            )}
        </>
    );
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
                            <InfoTip text={a.shown_because} />
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
                                <div className={styles.statuteRowHeader}>
                                    <span className={styles.statuteName}>{s.statute}</span>
                                    <InfoTip text={s.shown_because} />
                                </div>
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
                            <InfoTip text={c.shown_because} />
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
                            <InfoTip text={g.shown_because} />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// ── Deadline countdown helper ──────────────────────────────────────────────

function daysUntil(dateStr: string): number | null {
    try {
        const target = new Date(dateStr + 'T00:00:00');
        if (isNaN(target.getTime())) return null;
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    } catch {
        return null;
    }
}

function formatCountdown(days: number | null): string {
    if (days === null) return 'Date unclear';
    if (days < 0) return `${Math.abs(days)}d overdue`;
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days <= 30) return `${days} days`;
    const months = Math.floor(days / 30);
    return `${months}mo ${days % 30}d`;
}

function countdownClass(days: number | null): string {
    if (days === null) return styles.badgeMedium;
    if (days <= 7) return styles.badgeHigh;
    if (days <= 30) return styles.badgeMedium;
    return styles.badgeLow;
}

const DeadlinesCard: React.FC<{ items: Deadline[]; autoCollapsed?: boolean; onExpand?: () => void }> = ({ items, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };

    // Sort by date (soonest first)
    const sorted = [...items].sort((a, b) => {
        const da = daysUntil(a.date);
        const db = daysUntil(b.date);
        if (da === null && db === null) return 0;
        if (da === null) return 1;
        if (db === null) return -1;
        return da - db;
    });

    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiCalendarEvent className={styles.cardIcon} />
                    <span>Deadline Tracker</span>
                    <span className={styles.count}>{items.length}</span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {sorted.length === 0 ? (
                        <p className={styles.emptyText}>No deadlines detected in your documents.</p>
                    ) : (
                        sorted.map((d, i) => {
                            const days = daysUntil(d.date);
                            return (
                                <div key={i} className={styles.deadlineRow}>
                                    <span className={`${styles.badge} ${countdownClass(days)}`}>
                                        {formatCountdown(days)}
                                    </span>
                                    <div className={styles.deadlineText}>
                                        <span className={styles.deadlineTitle}>{d.title}</span>
                                        <span className={styles.deadlineDate}>{d.date} &middot; {d.source}</span>
                                        <span className={styles.deadlineDesc}>{d.description}</span>
                                    </div>
                                    <InfoTip text={d.shown_because} />
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};

const ConflictsCard: React.FC<{ items: Conflict[]; autoCollapsed?: boolean; onExpand?: () => void }> = ({ items, autoCollapsed, onExpand }) => {
    const [manualExpanded, setManualExpanded] = useState(true);
    const isOpen = autoCollapsed ? false : manualExpanded;
    const handleClick = () => {
        if (autoCollapsed && onExpand) { onExpand(); return; }
        setManualExpanded(!manualExpanded);
    };

    const conflictTypeLabel: Record<string, string> = {
        opposing_party: 'Opposing Party',
        shared_party: 'Shared Party',
        witness_overlap: 'Witness Overlap',
    };

    return (
        <div className={styles.card}>
            <div className={styles.cardHeader} onClick={handleClick}>
                <div className={styles.cardTitle}>
                    <BiShieldQuarter className={styles.cardIcon} />
                    <span>Conflict Check</span>
                    <span className={styles.count}>{items.length}</span>
                </div>
                {isOpen ? <BiChevronUp /> : <BiChevronDown />}
            </div>
            <div className={`${styles.cardBodyWrap} ${isOpen ? styles.cardBodyOpen : styles.cardBodyClosed}`}>
                <div className={styles.cardBody}>
                    {items.length === 0 ? (
                        <p className={styles.emptyText}>No conflicts detected across your documents.</p>
                    ) : (
                        items.map((c, i) => (
                            <div key={i} className={styles.conflictRow}>
                                <span className={`${styles.badge} ${priorityBadge[c.severity] ?? styles.badgeMedium}`}>
                                    {c.severity}
                                </span>
                                <div className={styles.conflictText}>
                                    <span className={styles.conflictParty}>{c.party_name}</span>
                                    <span className={styles.conflictType}>
                                        {conflictTypeLabel[c.conflict_type] || c.conflict_type}
                                    </span>
                                    <span className={styles.conflictDesc}>{c.description}</span>
                                    <span className={styles.conflictDocs}>
                                        Found in: {c.documents.join(', ')}
                                    </span>
                                </div>
                                <InfoTip text={c.shown_because} />
                            </div>
                        ))
                    )}
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
    onJurisdictionChange,
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

            // Notify parent of jurisdiction change
            if (onJurisdictionChange && data.jurisdiction) {
                onJurisdictionChange(data.jurisdiction);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load insights');
        } finally {
            setLoading(false);
        }
    }, [baseUrl, latestQuery, onJurisdictionChange]);

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

    // Map section names to their card components
    const sectionCards: Record<string, React.ReactNode> = insights ? {
        next_actions: <NextActionsCard key="next_actions" items={insights.next_actions} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
        related_statutes: <StatutesCard key="related_statutes" items={insights.related_statutes} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
        checklist: <ChecklistCard key="checklist" items={checklist} onToggle={handleChecklistToggle} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
        info_gaps: <InfoGapsCard key="info_gaps" items={insights.info_gaps} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
        deadlines: <DeadlinesCard key="deadlines" items={insights.deadlines || []} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
        conflicts: <ConflictsCard key="conflicts" items={insights.conflicts || []} autoCollapsed={autoCollapsed} onExpand={onExpand} />,
    } : {};

    // Determine which 4 sections to show
    const visibleSections = insights?.visible_sections || ['next_actions', 'related_statutes', 'checklist', 'info_gaps'];

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
                    {visibleSections.map((section) => sectionCards[section] || null)}
                </div>
            )}
        </div>
    );
};

export default ProactiveDashboard;

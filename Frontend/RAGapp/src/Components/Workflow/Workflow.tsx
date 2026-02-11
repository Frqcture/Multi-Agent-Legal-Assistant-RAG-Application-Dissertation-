import React, { useState, useEffect, useCallback } from 'react';
import styles from './Workflow.module.css';
import { BiBot, BiSearch, BiMessageDetail, BiBrain } from 'react-icons/bi';

// Types matching backend response
interface AgentStep {
    agent: 'planner' | 'retriever' | 'responder';
    message: string;
    timestamp: string;
    tool_calls: Array<{ tool: string; args: Record<string, unknown> }>;
    tool_results: Array<Record<string, unknown>>;
}

interface WorkflowState {
    workflow_id: string;
    query: string;
    user_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    steps: AgentStep[];
    answer: string | null;
    error: string | null;
    created_at: string;
    completed_at: string | null;
}

interface WorkflowProps {
    baseUrl: string;
}

const CSRF_COOKIE_NAME = 'csrf_token';

function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop()?.split(';').shift() ?? null;
    }
    return null;
}

const agentIcons: Record<string, React.ReactNode> = {
    planner: <BiBrain />,
    retriever: <BiSearch />,
    responder: <BiMessageDetail />,
};

const agentStyles: Record<string, string> = {
    planner: styles.stepPlanner,
    retriever: styles.stepRetriever,
    responder: styles.stepResponder,
};

const statusStyles: Record<string, string> = {
    pending: styles.statusPending,
    running: styles.statusRunning,
    completed: styles.statusCompleted,
    failed: styles.statusFailed,
};

export const WorkflowPanel: React.FC<{ workflow: WorkflowState }> = ({ workflow }) => {
    return (
        <div className={styles.workflowContainer}>
            <div className={styles.workflowHeader}>
                <div className={styles.workflowTitle}>
                    <BiBot /> Multi-Agent Workflow
                </div>
                <span className={`${styles.statusBadge} ${statusStyles[workflow.status]}`}>
                    {workflow.status}
                </span>
            </div>

            <div className={styles.stepsTimeline}>
                {workflow.steps.map((step, idx) => (
                    <div key={idx} className={styles.step}>
                        <div className={`${styles.stepIcon} ${agentStyles[step.agent]}`}>
                            {agentIcons[step.agent]}
                        </div>
                        <div className={styles.stepContent}>
                            <div className={styles.stepAgent}>{step.agent}</div>
                            <div className={styles.stepMessage}>{step.message}</div>
                            {step.tool_calls.length > 0 && (
                                <div className={styles.toolInfo}>
                                    {step.tool_calls.map((tc, i) => (
                                        <div key={i} className={styles.toolCall}>
                                            → {tc.tool}({Object.keys(tc.args).join(', ')})
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className={styles.stepTime}>
                                {new Date(step.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {workflow.answer && (
                <div className={styles.answerSection}>
                    <div className={styles.answerLabel}>Final Answer</div>
                    <div className={styles.answerText}>{workflow.answer}</div>
                </div>
            )}

            {workflow.error && (
                <div className={styles.errorSection}>
                    Error: {workflow.error}
                </div>
            )}
        </div>
    );
};

export const useWorkflow = (baseUrl: string) => {
    const [isRunning, setIsRunning] = useState(false);
    const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
    const [error, setError] = useState<string | null>(null);

    const startWorkflow = useCallback(async (question: string) => {
        setIsRunning(true);
        setError(null);
        setWorkflow(null);

        try {
            const csrfToken = getCookie(CSRF_COOKIE_NAME);
            const headers: Record<string, string> = { 'Content-Type': 'application/json' };
            if (csrfToken) {
                headers['X-CSRF-Token'] = csrfToken;
            }
            // Start workflow
            const startRes = await fetch(`${baseUrl}/workflow/start`, {
                method: 'POST',
                headers,
                credentials: 'include',
                body: JSON.stringify({ question }),
            });

            if (!startRes.ok) {
                throw new Error(`Failed to start workflow: ${startRes.status}`);
            }

            const { workflow_id } = await startRes.json();

            // Poll for status
            const poll = async () => {
                const statusRes = await fetch(`${baseUrl}/workflow/status/${workflow_id}`, {
                    credentials: 'include',
                });

                if (!statusRes.ok) {
                    throw new Error(`Failed to get status: ${statusRes.status}`);
                }

                const state: WorkflowState = await statusRes.json();
                setWorkflow(state);

                if (state.status === 'pending' || state.status === 'running') {
                    // Continue polling
                    setTimeout(poll, 1000);
                } else {
                    // Completed or failed
                    setIsRunning(false);
                }
            };

            // Start polling
            await poll();

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            setIsRunning(false);
        }
    }, [baseUrl]);

    return { workflow, isRunning, error, startWorkflow };
};

export const WorkflowTrigger: React.FC<{
    baseUrl: string;
    question: string;
    onComplete?: (workflow: WorkflowState) => void;
}> = ({ baseUrl, question, onComplete }) => {
    const { workflow, isRunning, error, startWorkflow } = useWorkflow(baseUrl);
    const [hasCalledComplete, setHasCalledComplete] = useState(false);

    // Reset the flag when a new workflow starts
    useEffect(() => {
        if (isRunning) {
            setHasCalledComplete(false);
        }
    }, [isRunning]);

    useEffect(() => {
        if (workflow?.status === 'completed' && onComplete && !hasCalledComplete) {
            setHasCalledComplete(true);
            onComplete(workflow);
        }
    }, [workflow, onComplete, hasCalledComplete]);

    return (
        <div>
            <button
                className={styles.workflowTrigger}
                onClick={() => startWorkflow(question)}
                disabled={isRunning || !question.trim()}
            >
                {isRunning ? (
                    <>
                        <span className={styles.spinner} />
                        Running agents...
                    </>
                ) : (
                    <>
                        <BiBot /> Run Multi-Agent
                    </>
                )}
            </button>

            {error && <div className={styles.errorSection}>{error}</div>}

            {workflow && <WorkflowPanel workflow={workflow} />}
        </div>
    );
};

export default WorkflowTrigger;

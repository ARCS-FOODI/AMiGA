import React from 'react';

export default class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error(`[ErrorBoundary] Crash in ${this.props.section}:`, error, errorInfo);
        try {
            window.dispatchEvent(new CustomEvent('telemetry-metric', {
                detail: { 
                    filename: 'SYS_CRASH', 
                    kbSize: '0', 
                    level: 'error', 
                    message: `REACT CRASH [${this.props.section}]: ${error.message} | ${error.stack?.split('\\n')[1]?.trim()}`, 
                    time: new Date().toLocaleTimeString([], { hour12: false }) 
                }
            }));
        } catch(e) {}
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ 
                    padding: '1.5rem', 
                    border: '1px solid var(--accent-red)', 
                    color: 'var(--accent-red)', 
                    background: 'rgba(239,68,68,0.1)', 
                    borderRadius: '8px', 
                    margin: '1rem 0',
                    fontFamily: 'monospace'
                }}>
                    <strong>💥 CRASH in {this.props.section}</strong><br/><br/>
                    {this.state.error.message}
                </div>
            );
        }
        return this.props.children;
    }
}

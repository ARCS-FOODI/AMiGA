import { useState } from 'react';

export default function GrafanaPanel({ 
    src, 
    title = "Analytics", 
    height = "300px",
    dashboardUrl = "http://localhost:3000/d/ad6tm2x/amiga" 
}) {
    const [loading, setLoading] = useState(true);

    return (
        <div className="glass-card" style={{
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            minHeight: '200px',
            position: 'relative'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ color: 'var(--accent-teal)' }}>📊</span> {title}
                </h3>
                <a 
                    href={dashboardUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ 
                        fontSize: '0.75rem', 
                        color: 'var(--accent-blue)', 
                        textDecoration: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        background: 'rgba(14, 165, 233, 0.1)',
                        border: '1px solid rgba(14, 165, 233, 0.2)',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'rgba(14, 165, 233, 0.2)'}
                    onMouseLeave={(e) => e.target.style.background = 'rgba(14, 165, 233, 0.1)'}
                >
                    Full Dashboard ↗
                </a>
            </div>

            <div style={{ 
                width: '100%', 
                height: height, 
                borderRadius: '8px', 
                overflow: 'hidden', 
                background: 'rgba(0,0,0,0.2)',
                position: 'relative',
                border: loading ? '1px solid rgba(255,255,255,0.05)' : 'none'
            }}>
                {loading && (
                    <div style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-secondary)',
                        fontSize: '0.85rem',
                        zIndex: 1
                    }}>
                        Connecting to Grafana...
                    </div>
                )}
                <iframe
                    src={src}
                    width="100%"
                    height="100%"
                    frameBorder="0"
                    onLoad={() => setLoading(false)}
                    style={{ 
                        border: 'none',
                        opacity: loading ? 0 : 1,
                        transition: 'opacity 0.5s ease'
                    }}
                    title={title}
                ></iframe>
            </div>
        </div>
    );
}

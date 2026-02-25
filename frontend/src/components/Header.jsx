import { useState, useEffect } from 'react';
import { fetchConfig } from '../api';

export default function Header() {
    const [online, setOnline] = useState(false);
    const [time, setTime] = useState(new Date().toLocaleTimeString());

    useEffect(() => {
        // Check API health
        fetchConfig()
            .then(() => setOnline(true))
            .catch(() => setOnline(false));

        // Update real-time clock
        const timer = setInterval(() => {
            setTime(new Date().toLocaleTimeString());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <header className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', padding: '1rem 2rem' }}>
            <h1 style={{ background: 'linear-gradient(90deg, #38bdf8, #8b5cf6)', WebkitBackgroundClip: 'text', color: 'transparent', margin: 0 }}>
                AMiGA OS
            </h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                <div style={{ fontSize: '1.2rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {time}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <span className={`status-indicator ${online ? 'status-online' : 'status-offline'}`}></span>
                    {online ? 'System Online' : 'System Offline (API Unreachable)'}
                </div>
            </div>
        </header>
    );
}

import { useState, useEffect } from 'react';
import { stopAllPumps, unlockAllPumps, getPumpsStatus } from '../api';
import { POLL_INTERVALS } from '../polling';

export default function PumpEmergencyControl() {
    const [locked, setLocked] = useState(false);
    const [runningPumps, setRunningPumps] = useState([]);

    const checkStatus = async () => {
        try {
            const status = await getPumpsStatus();
            setLocked(status.locked);
            setRunningPumps(status.running_pumps || []);
        } catch (e) {
            console.error("Failed to fetch pump status", e);
        }
    };

    useEffect(() => {
        checkStatus();
        const interval = setInterval(checkStatus, POLL_INTERVALS.STATUS);

        const handleRefresh = () => checkStatus();
        window.addEventListener('amiga-refresh-sensors', handleRefresh);

        return () => {
            clearInterval(interval);
            window.removeEventListener('amiga-refresh-sensors', handleRefresh);
        };
    }, []);

    const handleStop = async () => {
        await stopAllPumps();
        window.dispatchEvent(new Event('amiga-refresh-sensors'));
    };

    const handleUnlock = async () => {
        await unlockAllPumps();
        window.dispatchEvent(new Event('amiga-refresh-sensors'));
    };

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2', borderColor: locked ? 'var(--accent-red)' : 'var(--glass-border)', boxShadow: locked ? '0 0 15px rgba(239, 68, 68, 0.2)' : 'var(--glass-shadow)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h3 style={{ color: locked ? 'var(--accent-red)' : 'inherit', margin: 0 }}>
                        🚨 Emergency Pump Control
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>
                        {locked ? 'All motor operations are currently LOCKED. Background tasks paused.' : 'System normal. Motors are unlocked and available.'}
                    </p>
                </div>

                {locked ? (
                    <button
                        onClick={handleUnlock}
                        style={{ backgroundColor: 'var(--accent-green)', padding: '0.8rem 1.5rem', fontWeight: 'bold' }}
                    >
                        🔓 UNLOCK SYSTEM
                    </button>
                ) : (
                    <button
                        onClick={handleStop}
                        style={{ backgroundColor: 'var(--accent-red)', padding: '0.8rem 1.5rem', fontWeight: 'bold', animation: runningPumps.length > 0 ? 'pulse 1s infinite' : 'none' }}
                    >
                        🛑 STOP ALL PUMPS
                    </button>
                )}
            </div>

            {!locked && runningPumps.length > 0 && (
                <div style={{ marginTop: '1rem', color: 'var(--accent-yellow)', fontSize: '0.85rem' }}>
                    Active Pumps: {runningPumps.join(', ')}
                </div>
            )}
        </div>
    );
}

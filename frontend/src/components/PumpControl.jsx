import { useState, useEffect } from 'react';
import { runPumpMl, runPumpSeconds, getPumpsStatus } from '../api';
import { POLL_INTERVALS } from '../polling';

export default function PumpControl({ pumpName, colorBase = 'var(--accent-blue)', hoverBase = '#3b82f6' }) {
    const [ml, setMl] = useState('50');
    const [seconds, setSeconds] = useState('5');
    const [running, setRunning] = useState(false);
    const [error, setError] = useState(null);
    const [hzMode, setHzMode] = useState('preset');
    const [presetHz, setPresetHz] = useState('10000');
    const [customHz, setCustomHz] = useState('10000');
    const [locked, setLocked] = useState(false);
    const [elapsed, setElapsed] = useState(0);

    useEffect(() => {
        let timer;
        if (running) {
            setElapsed(0);
            const startTime = Date.now();
            timer = setInterval(() => {
                setElapsed(((Date.now() - startTime) / 1000).toFixed(1));
            }, 100);
        } else {
            setElapsed(0);
        }
        return () => clearInterval(timer);
    }, [running]);

    useEffect(() => {
        const checkLock = async () => {
            try {
                const status = await getPumpsStatus();
                setLocked(status.locked);
            } catch(e) {}
        }
        checkLock();
        const interval = setInterval(checkLock, POLL_INTERVALS.STATUS);
        window.addEventListener('amiga-refresh-sensors', checkLock);
        return () => {
            clearInterval(interval);
            window.removeEventListener('amiga-refresh-sensors', checkLock);
        }
    }, []);

    const getActiveHz = () => {
        return hzMode === 'preset' ? parseFloat(presetHz) : parseFloat(customHz);
    };

    const handleRunMl = async (dir = 'forward') => {
        setRunning(true);
        setError(null);
        try {
            await runPumpMl(pumpName, parseFloat(ml), getActiveHz(), dir);
        } catch (err) {
            setError(err.message);
        } finally {
            setRunning(false);
        }
    };

    const handleRunSecs = async (dir = 'forward') => {
        setRunning(true);
        setError(null);
        try {
            await runPumpSeconds(pumpName, parseFloat(seconds), getActiveHz(), dir);
        } catch (err) {
            setError(err.message);
        } finally {
            setRunning(false);
        }
    };

    return (
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
            {running && (
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '4px', background: colorBase, animation: 'pulse 1s infinite' }} />
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ textTransform: 'capitalize' }}>💧 {pumpName} Reservoir</h3>
                <span className={`status-indicator ${running ? 'status-online' : 'status-neutral'}`} style={{ backgroundColor: running ? colorBase : '' }}></span>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}
            {locked && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem', fontWeight: 'bold' }}>SYSTEM LOCKED</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem', opacity: locked ? 0.5 : 1 }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Step Frequency (Torque / Speed)</label>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <select
                        value={hzMode === 'preset' ? presetHz : 'custom'}
                        onChange={(e) => {
                            if (e.target.value === 'custom') {
                                setHzMode('custom');
                            } else {
                                setHzMode('preset');
                                setPresetHz(e.target.value);
                            }
                        }}
                        disabled={running || locked}
                        style={{ flex: hzMode === 'custom' ? 1 : 2 }}
                    >
                        <option value="10000">10 kHz (Default / High Torque)</option>
                        <option value="30000">30 kHz (Balanced)</option>
                        <option value="50000">50 kHz (High Speed)</option>
                        <option value="custom">Custom...</option>
                    </select>

                    {hzMode === 'custom' && (
                        <input
                            type="number"
                            value={customHz}
                            onChange={e => setCustomHz(e.target.value)}
                            disabled={running || locked}
                            style={{ flex: 1 }}
                            placeholder="Hz"
                        />
                    )}
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                    <div style={{ flex: 2 }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Dispense Volume (mL)</label>
                        <input
                            type="number"
                            value={ml}
                            onChange={e => setMl(e.target.value)}
                            disabled={running || locked}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ display: 'flex', flex: 2, gap: '0.5rem' }}>
                        <button
                            onClick={() => handleRunMl('forward')}
                            disabled={running || locked}
                            style={{ flex: 1, backgroundColor: colorBase, padding: '0.5rem' }}
                            title="Forward"
                        >
                            Fwd
                        </button>
                        <button
                            onClick={() => handleRunMl('reverse')}
                            disabled={running || locked}
                            style={{ flex: 1, backgroundColor: 'transparent', color: 'var(--text-primary)', border: `1px solid ${colorBase}`, padding: '0.5rem' }}
                            title="Reverse"
                        >
                            Rev
                        </button>
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', margin: '0.25rem 0' }}>
                    <hr style={{ flex: 1, border: 'none', borderTop: '1px solid var(--glass-border)' }} />
                    <span style={{ 
                        margin: '0 1rem', 
                        fontSize: '0.75rem', 
                        color: running ? 'var(--accent-yellow)' : 'var(--text-secondary)',
                        fontFamily: 'monospace'
                    }}>
                        {running ? `Elapsed: ${elapsed}s` : ''}
                    </span>
                    <hr style={{ flex: 1, border: 'none', borderTop: '1px solid var(--glass-border)' }} />
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                    <div style={{ flex: 2 }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Manual Prime (Sec)</label>
                        <input
                            type="number"
                            value={seconds}
                            onChange={e => setSeconds(e.target.value)}
                            disabled={running || locked}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ display: 'flex', flex: 2, gap: '0.5rem' }}>
                        <button
                            onClick={() => handleRunSecs('forward')}
                            disabled={running || locked}
                            style={{ flex: 1, padding: '0.5rem' }}
                            title="Forward"
                        >
                            Fwd
                        </button>
                        <button
                            onClick={() => handleRunSecs('reverse')}
                            disabled={running || locked}
                            style={{ flex: 1, backgroundColor: 'transparent', border: '1px solid var(--text-secondary)', color: 'var(--text-secondary)', padding: '0.5rem' }}
                            title="Reverse"
                        >
                            Rev
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

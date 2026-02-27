import { useState } from 'react';
import { runPumpMl, runPumpSeconds } from '../api';

export default function PumpControl({ pumpName, colorBase = 'var(--accent-blue)', hoverBase = '#3b82f6' }) {
    const [ml, setMl] = useState('50');
    const [seconds, setSeconds] = useState('5');
    const [running, setRunning] = useState(false);
    const [error, setError] = useState(null);

    const handleRunMl = async () => {
        setRunning(true);
        setError(null);
        try {
            await runPumpMl(pumpName, parseFloat(ml));
        } catch (err) {
            setError(err.message);
        } finally {
            setRunning(false);
        }
    };

    const handleRunSecs = async () => {
        setRunning(true);
        setError(null);
        try {
            await runPumpSeconds(pumpName, parseFloat(seconds));
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
                <h3 style={{ textTransform: 'capitalize' }}>💧 {pumpName} isaac is awesome!</h3>
                <span className={`status-indicator ${running ? 'status-online' : 'status-neutral'}`} style={{ backgroundColor: running ? colorBase : '' }}></span>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                    <div style={{ flex: 2 }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Dispense Volume (mL)</label>
                        <input
                            type="number"
                            value={ml}
                            onChange={e => setMl(e.target.value)}
                            disabled={running}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <button
                        onClick={handleRunMl}
                        disabled={running}
                        style={{ flex: 1, backgroundColor: colorBase }}
                    >
                        {running ? 'Running...' : 'Run'}
                    </button>
                </div>

                <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)' }} />

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                    <div style={{ flex: 2 }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Manual Prime (Sec)</label>
                        <input
                            type="number"
                            value={seconds}
                            onChange={e => setSeconds(e.target.value)}
                            disabled={running}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <button
                        onClick={handleRunSecs}
                        disabled={running}
                        style={{ flex: 1 }}
                    >
                        Purge
                    </button>
                </div>
            </div>
        </div>
    );
}

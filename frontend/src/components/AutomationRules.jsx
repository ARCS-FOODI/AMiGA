import { useState } from 'react';
import { runControlCycle } from '../api';

export default function AutomationRules() {
    const [params, setParams] = useState({
        pump: 'water',
        target_threshold: 2.0,
        vote_k: 2,
        irrigate_seconds: 5.0
    });

    const [running, setRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleTestCycle = async () => {
        setRunning(true);
        setResult(null);
        setError(null);
        try {
            const res = await runControlCycle(params);
            setResult(res);
        } catch (err) {
            setError(err.message);
        } finally {
            setRunning(false);
        }
    };

    return (
        <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>⚙️ Automation Console</h3>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ flex: '1 1 200px' }}>
                    <label style={{ fontSize: '0.85rem' }}>Target Pump</label>
                    <select
                        value={params.pump}
                        onChange={e => setParams({ ...params, pump: e.target.value })}
                        style={{ width: '100%', padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '4px' }}
                    >
                        <option value="water">Water</option>
                        <option value="food">Food</option>
                    </select>
                </div>

                <div style={{ flex: '1 1 200px' }}>
                    <label style={{ fontSize: '0.85rem' }}>Dry Threshold (V)</label>
                    <input
                        type="number"
                        step="0.1"
                        value={params.target_threshold}
                        onChange={e => setParams({ ...params, target_threshold: parseFloat(e.target.value) })}
                        style={{ width: '100%' }}
                    />
                </div>

                <div style={{ flex: '1 1 200px' }}>
                    <label style={{ fontSize: '0.85rem' }}>Required Votes</label>
                    <input
                        type="number"
                        min="1" max="4"
                        value={params.vote_k}
                        onChange={e => setParams({ ...params, vote_k: parseInt(e.target.value) })}
                        style={{ width: '100%' }}
                    />
                </div>

                <div style={{ flex: '1 1 200px' }}>
                    <label style={{ fontSize: '0.85rem' }}>Irrigate Duration (Sec)</label>
                    <input
                        type="number"
                        step="1"
                        value={params.irrigate_seconds}
                        onChange={e => setParams({ ...params, irrigate_seconds: parseFloat(e.target.value) })}
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            <button className="primary" onClick={handleTestCycle} disabled={running} style={{ width: '100%', padding: '1rem' }}>
                {running ? 'Evaluating Logic...' : 'Force Evaluation Cycle'}
            </button>

            {error && <div style={{ color: 'var(--accent-red)', marginTop: '1rem' }}>{error}</div>}

            {result && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                    <h4 style={{ marginBottom: '0.5rem', color: result.triggered ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
                        Result: {result.triggered ? `IRRIGATED (${result.pump_action?.seconds}s)` : 'NO ACTION (Soil Moist)'}
                    </h4>
                    <pre style={{ margin: 0, fontSize: '0.8rem', overflowX: 'auto', color: 'var(--text-secondary)' }}>
                        Sensors &gt; {params.target_threshold}V: {result.under_threshold_count} (Needed {params.vote_k})
                    </pre>
                </div>
            )}
        </div>
    );
}

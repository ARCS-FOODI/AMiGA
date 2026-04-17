import { useState, useEffect } from 'react';
import { getRecordingStatus, startRecording, stopRecording, getRecipeStatus } from '../api';

export default function RecordingButton() {
    const [isRecording, setIsRecording] = useState(false);
    const [isCycling, setIsCycling] = useState(false);
    const [sessionDir, setSessionDir] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showSettings, setShowSettings] = useState(false);

    // Frequencies state
    const [freqs, setFreqs] = useState({
        scale: 5.0,
        sis: 5.0,
        sensors: 10.0,
        co2: 10.0,
        light: 10.0,
        light_status: 10.0,
        pump_status: 5.0
    });

    const fetchStatus = async () => {
        try {
            const [recStatus, growStatus] = await Promise.all([
                getRecordingStatus(),
                getRecipeStatus()
            ]);
            setIsRecording(recStatus.is_recording);
            setSessionDir(recStatus.session_dir);
            setIsCycling(growStatus.is_cycling);
        } catch (err) {
            setError("Cannot connect to recording service.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        // Load saved defaults if they exist
        const savedPrefs = localStorage.getItem("amiga_recording_freqs");
        if (savedPrefs) {
            try {
                setFreqs(JSON.parse(savedPrefs));
            } catch (e) { }
        }

        // Auto poll status
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const toggleRecording = async () => {
        if (isRecording && isCycling) {
            const confirmed = window.confirm(
                "⚠️ ATTENTION: A Growth Lifecycle is currently ACTIVE.\n\n" +
                "Stopping recording now will result in missing telemetry for this live cycle. " +
                "It is recommended to stop the Growth Lifecycle Hub first if the experiment is finished.\n\n" +
                "Do you still want to stop recording?"
            );
            if (!confirmed) return;
        }

        setLoading(true);
        setError(null);
        try {
            if (isRecording) {
                await stopRecording();
                setIsRecording(false);
                setSessionDir(null);
            } else {
                const res = await startRecording(freqs);
                setIsRecording(true);
                setSessionDir(res.session_dir);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveDefaults = () => {
        localStorage.setItem("amiga_recording_freqs", JSON.stringify(freqs));
        alert("Defaults saved locally!");
    };

    const handleFreqChange = (key, value) => {
        setFreqs(prev => ({ ...prev, [key]: parseFloat(value) || 1.0 }));
    };

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2', borderColor: isRecording ? 'var(--accent-red)' : 'var(--glass-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div
                        style={{
                            width: '16px', height: '16px', borderRadius: '50%',
                            background: isRecording ? 'var(--accent-red)' : 'grey',
                            boxShadow: isRecording ? '0 0 12px var(--accent-red)' : 'none',
                            animation: isRecording ? 'pulse 2s infinite' : 'none'
                        }}
                    ></div>
                    <div>
                        <h3 style={{ margin: 0 }}>Data Recording</h3>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                            {isRecording
                                ? `Recording to: ${sessionDir ? sessionDir.split('/').pop() : '...'}`
                                : 'System Idle'}
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        className="btn-secondary"
                        onClick={() => setShowSettings(!showSettings)}
                        disabled={loading || isRecording}
                    >
                        ⚙️ Settings
                    </button>
                    <button
                        onClick={toggleRecording}
                        disabled={loading}
                        style={{
                            background: isRecording ? 'transparent' : 'var(--accent-red)',
                            border: isRecording ? '2px solid var(--accent-red)' : 'none',
                            color: isRecording ? 'var(--accent-red)' : '#fff',
                            fontWeight: 'bold',
                            padding: '0.5rem 1.5rem',
                            borderRadius: '20px'
                        }}
                    >
                        {loading ? 'Wait...' : isRecording ? 'Stop Recording' : '⏺ Start Record'}
                    </button>
                </div>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginTop: '1rem' }}>⚠️ {error}</div>}

            {showSettings && !isRecording && (
                <div style={{ marginTop: '1.5rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px' }}>
                    <h4 style={{ margin: '0 0 1rem 0' }}>Polling Interval Settings (Seconds)</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                        {Object.keys(freqs).map(key => (
                            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                    {key.replace('_', ' ')}
                                </label>
                                <input
                                    type="number"
                                    min="0.1"
                                    step="0.1"
                                    value={freqs[key]}
                                    onChange={(e) => handleFreqChange(key, e.target.value)}
                                    style={{
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'white',
                                        padding: '0.4rem',
                                        borderRadius: '4px'
                                    }}
                                />
                            </div>
                        ))}
                    </div>
                    <button className="btn-secondary" onClick={handleSaveDefaults} style={{ width: '100%' }}>
                        💾 Save Defaults
                    </button>
                </div>
            )}
        </div>
    );
}

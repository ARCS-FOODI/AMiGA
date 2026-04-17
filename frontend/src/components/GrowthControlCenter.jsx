import { useState, useEffect } from 'react';
import { getRecipe, getRecipeStatus, saveRecipe, startRecording, getRecordingStatus } from '../api';

export default function GrowthControlCenter() {
    const [status, setStatus] = useState(null);
    const [recording, setRecording] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const [sData, recData] = await Promise.all([getRecipeStatus(), getRecordingStatus()]);
            setStatus(sData);
            setRecording(recData.is_recording);
        } catch (err) {
            // silent
        }
    };

    const handleStartCycle = async () => {
        setSaving(true);
        setError(null);
        try {
            const recipe = await getRecipe();
            if (!recipe) throw new Error("No recipe configured to start.");
            
            const newRecipe = { ...recipe, created_at: new Date().toISOString() };
            await saveRecipe(newRecipe);
            await startRecording({}, newRecipe.name); // Start CSV telemetry automatically
            await fetchStatus();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const currentDay = status?.current_day || 0;
    const activePhase = status?.phase?.name || "None";
    const daemonActive = status?.active;

    return (
        <div style={{ 
            background: 'rgba(0,0,0,0.4)', 
            borderRadius: '12px', 
            border: '1px solid var(--glass-border)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            height: '100%'
        }}>
            {/* Background glowing image */}
            <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundImage: 'url(/plant_graphic.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                opacity: 0.15,
                zIndex: 0,
                pointerEvents: 'none'
            }}></div>

            <div style={{ position: 'relative', zIndex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
                    
                    <div>
                        <h3 style={{ margin: '0 0 1rem 0', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.4rem', textShadow: '0 0 15px rgba(16, 185, 129, 0.4)' }}>
                            🌱 Growth Lifecycle Hub
                        </h3>
                        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                            {/* Daemon Status */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Automation Engine</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: daemonActive ? 'var(--accent-green)' : 'var(--accent-red)', boxShadow: daemonActive ? '0 0 8px var(--accent-green)' : 'none' }}></div>
                                    <strong style={{ color: daemonActive ? 'var(--accent-green)' : 'var(--accent-red)' }}>{daemonActive ? 'ONLINE' : 'OFFLINE'}</strong>
                                </div>
                            </div>
                            
                            {/* Recording Status */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>CSV Telemetry</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <div className={recording ? 'pulse-rec' : ''} style={{ width: '12px', height: '12px', borderRadius: '50%', background: recording ? 'var(--accent-red)' : 'var(--text-secondary)', boxShadow: recording ? '0 0 10px var(--accent-red)' : 'none' }}></div>
                                    <strong style={{ color: recording ? 'var(--accent-red)' : 'var(--text-secondary)' }}>{recording ? 'RECORDING' : 'STANDBY'}</strong>
                                </div>
                            </div>

                            {/* Cycle Timeline */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Timeline</span>
                                <div style={{ fontSize: '1rem' }}>
                                    Day <strong style={{ color: 'white', fontSize: '1.2rem' }}>{currentDay}</strong> / <span style={{ color: 'var(--accent-teal)' }}>Phase: {activePhase}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Integrated Start Button */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem', flex: 1, minWidth: '250px' }}>
                        <button onClick={handleStartCycle} disabled={saving} 
                            style={{ 
                                padding: '1.2rem 2rem', 
                                fontSize: '1.2rem', 
                                background: 'var(--accent-green)', 
                                color: '#000', 
                                fontWeight: '900', 
                                borderRadius: '8px',
                                boxShadow: '0 0 25px rgba(16, 185, 129, 0.4)',
                                border: '2px solid #059669',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                textTransform: 'uppercase',
                                letterSpacing: '1px',
                                width: '100%'
                            }}>
                            {saving ? 'INITIALIZING...' : '▶ START GROWTH CYCLE'}
                        </button>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textAlign: 'right', display: 'block' }}>
                            Automatically resets recipe to Day 0 and engages backend sensory telemetry.
                        </span>
                        {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.8rem', marginTop: '0.5rem' }}>{error}</div>}
                    </div>

                </div>
            </div>
        </div>
    );
}

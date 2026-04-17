import { useState, useEffect } from 'react';
import { getRecipe, getRecipeStatus, saveRecipe, startRecording, getRecordingStatus, stopRecording, stopCycle } from '../api';

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

    const handleStopCycle = async () => {
        if (!window.confirm("Are you sure you want to TERMINATE the current growth cycle? This stops automation and telemetry.")) return;
        setSaving(true);
        try {
            await stopCycle();
            await stopRecording();
            await fetchStatus();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const currentDay = status?.current_day || 0;
    const totalDays = status?.total_days || 0;
    const activePhase = status?.phase?.name || "None";
    const daemonActive = status?.active;
    const isCycling = status?.is_cycling;
    const createdAt = status?.created_at;

    // Calculate duration since start
    const [duration, setDuration] = useState("");

    useEffect(() => {
        if (!createdAt || !isCycling) {
            setDuration("");
            return;
        }

        const updateClock = () => {
            const start = new Date(createdAt);
            const now = new Date();
            const diffMs = now - start;
            if (diffMs < 0) return setDuration("Initializing...");

            const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            
            setDuration(`${days}d ${hours}h ${mins}m`);
        };

        updateClock();
        const clockInterval = setInterval(updateClock, 30000); // update every 30s
        return () => clearInterval(clockInterval);
    }, [createdAt, isCycling]);

    const progressPercent = totalDays > 0 ? Math.min(100, (currentDay / totalDays) * 100) : 0;

    return (
        <div style={{ 
            background: 'rgba(0,0,0,0.4)', 
            borderRadius: '12px', 
            border: isCycling ? '1px solid var(--accent-green)' : '1px solid var(--glass-border)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            transition: 'all 0.5s ease',
            boxShadow: isCycling ? '0 0 30px rgba(16, 185, 129, 0.15), inset 0 0 20px rgba(16, 185, 129, 0.05)' : 'none',
            animation: isCycling ? 'breathing-glow 4s infinite ease-in-out' : 'none'
        }}>
            <style>
                {`
                    @keyframes breathing-glow {
                        0% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.1), inset 0 0 10px rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.4); }
                        50% { box-shadow: 0 0 40px rgba(16, 185, 129, 0.25), inset 0 0 30px rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.8); }
                        100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.1), inset 0 0 10px rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.4); }
                    }
                    @keyframes pulse-live {
                        0% { opacity: 0.5; transform: scale(0.95); }
                        50% { opacity: 1; transform: scale(1.05); }
                        100% { opacity: 0.5; transform: scale(0.95); }
                    }
                `}
            </style>

            {/* Background glowing image */}
            <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundImage: 'url(/plant_graphic.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                opacity: isCycling ? 0.25 : 0.15,
                zIndex: 0,
                pointerEvents: 'none',
                transition: 'opacity 1s ease'
            }}></div>

            <div style={{ position: 'relative', zIndex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
                    
                    <div style={{ flex: 2 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', margin: '0 0 1rem 0' }}>
                            <h3 style={{ margin: 0, color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.4rem', textShadow: '0 0 15px rgba(16, 185, 129, 0.4)' }}>
                                🌱 Growth Lifecycle Hub
                            </h3>
                            {isCycling && (
                                <div style={{ 
                                    background: 'rgba(16, 185, 129, 0.2)', 
                                    color: 'var(--accent-green)', 
                                    padding: '2px 10px', 
                                    borderRadius: '20px', 
                                    fontSize: '0.7rem', 
                                    fontWeight: 'bold', 
                                    border: '1px solid var(--accent-green)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '5px',
                                    animation: 'pulse-live 2s infinite ease-in-out'
                                }}>
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 5px var(--accent-green)' }}></div>
                                    LIVE CYCLE ACTIVE
                                </div>
                            )}
                        </div>

                        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                            {/* Daemon Status */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>System Server</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: daemonActive ? 'var(--accent-green)' : 'var(--accent-red)', boxShadow: daemonActive ? '0 0 8px var(--accent-green)' : 'none' }}></div>
                                    <strong style={{ color: daemonActive ? 'var(--accent-green)' : 'var(--accent-red)', fontSize: '0.9rem' }}>{daemonActive ? 'ONLINE' : 'OFFLINE'}</strong>
                                </div>
                            </div>
                            
                            {/* Recording Status */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>CSV Telemetry</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <div className={recording ? 'pulse-rec' : ''} style={{ width: '10px', height: '10px', borderRadius: '50%', background: recording ? 'var(--accent-red)' : 'var(--text-secondary)', boxShadow: recording ? '0 0 10px var(--accent-red)' : 'none' }}></div>
                                    <strong style={{ color: recording ? 'var(--accent-red)' : 'var(--text-secondary)', fontSize: '0.9rem' }}>{recording ? 'RECORDING' : 'STANDBY'}</strong>
                                </div>
                            </div>

                            {/* Cycle Timeline */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', minWidth: '150px' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Timeline</span>
                                <div style={{ fontSize: '0.9rem' }}>
                                    Day <strong style={{ color: 'white', fontSize: '1.1rem' }}>{currentDay}</strong> / <span style={{ color: isCycling ? 'var(--accent-teal)' : 'var(--text-secondary)' }}>Phase: {activePhase}</span>
                                </div>
                                {isCycling && (
                                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginTop: '4px', overflow: 'hidden' }}>
                                        <div style={{ width: `${progressPercent}%`, height: '100%', background: 'var(--accent-teal)', transition: 'width 1s ease-out' }}></div>
                                    </div>
                                )}
                            </div>

                            {/* Session Age */}
                            {isCycling && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Cycle Age</span>
                                    <div style={{ fontSize: '0.9rem', color: 'white', fontWeight: 'bold' }}>
                                        {duration}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Integrated Start Button */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem', flex: 1, minWidth: '250px' }}>
                        <button onClick={handleStartCycle} disabled={saving} 
                            style={{ 
                                padding: '1.2rem 2rem', 
                                fontSize: '1.2rem', 
                                background: isCycling ? 'rgba(16, 185, 129, 0.1)' : 'var(--accent-green)', 
                                color: isCycling ? 'var(--accent-green)' : '#000', 
                                fontWeight: '900', 
                                borderRadius: '8px',
                                boxShadow: isCycling ? 'none' : '0 0 25px rgba(16, 185, 129, 0.4)',
                                border: isCycling ? '2px solid var(--accent-green)' : '2px solid #059669',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                textTransform: 'uppercase',
                                letterSpacing: '1px',
                                width: '100%'
                            }}>
                            {saving ? 'INITIALIZING...' : isCycling ? '↺ RESTART GROWTH CYCLE' : '▶ START GROWTH CYCLE'}
                        </button>
                        
                        {isCycling && (
                            <button onClick={handleStopCycle} disabled={saving} 
                                style={{ 
                                    padding: '0.8rem 1.5rem', 
                                    fontSize: '0.9rem', 
                                    background: 'rgba(239, 68, 68, 0.1)', 
                                    color: 'var(--accent-red)', 
                                    fontWeight: 'bold', 
                                    borderRadius: '6px',
                                    border: '1px solid var(--accent-red)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    textTransform: 'uppercase',
                                    width: '100%',
                                    marginTop: '0.5rem'
                                }}>
                                ⏹ STOP GROWTH CYCLE
                            </button>
                        )}

                        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textAlign: 'right', display: 'block' }}>
                            {isCycling ? 'Redeploys current recipe to Day 0 and restarts recording session.' : 'Automatically resets recipe to Day 0 and engages backend sensory telemetry.'}
                        </span>
                        {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.8rem', marginTop: '0.5rem' }}>{error}</div>}
                    </div>

                </div>
            </div>
        </div>
    );
}

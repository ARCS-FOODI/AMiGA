import { useState, useEffect, useMemo, useCallback } from 'react';
import { 
    ResponsiveContainer, 
    LineChart, 
    Line, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip, 
    Legend 
} from 'recharts';
import Papa from 'papaparse';
import { fetchTelemetry } from '../api';

/**
 * TelemetryChart - A reusable chart component that fetches and parses CSV data.
 * @param {string} filename - The CSV filename to fetch (e.g., 'sensors.csv')
 * @param {string} title - Chart title
 * @param {string[]} dataKeys - The columns to display as lines
 * @param {string[]} colors - Colors for each line
 * @param {Object} filter - Optional filter object (e.g. { device_id: 'ADS1115_0x48' })
 * @param {boolean} isComparative - If true, merges rows by timestamp across multiple devices
 * @param {number} historyHours - How many hours of data to show (default 4)
 * @param {number} refreshInterval - Refresh rate in ms (default 10000)
 */
export default function TelemetryChart({ 
    filename, 
    title = "Telemetry", 
    dataKeys = ["v0"], 
    colors = ["var(--accent-teal)"],
    filter = null,
    isComparative = false,
    historyHours = 4,
    refreshInterval = 10000 
}) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [hiddenKeys, setHiddenKeys] = useState([]);

    const toggleLine = (e) => {
        const { dataKey } = e;
        setHiddenKeys(prev => 
            prev.includes(dataKey) ? prev.filter(k => k !== dataKey) : [...prev, dataKey]
        );
    };

    // Derived device label for visual verification
    const deviceTag = useMemo(() => {
        if (!filter || isComparative) return null;
        return Object.values(filter).join(', ');
    }, [filter, isComparative]);

    const pullData = useCallback(async () => {
        try {
            const csvText = await fetchTelemetry(filename);
            const parsed = Papa.parse(csvText, { 
                header: true, 
                dynamicTyping: true,
                skipEmptyLines: true 
            });

            if (parsed.errors.length > 0 && parsed.data.length === 0) {
                throw new Error("Failed to parse CSV data.");
            }

            // Filter for last N hours first (Performance)
            const now = new Date();
            const cutoff = now.getTime() - (historyHours * 60 * 60 * 1000);
            
            let sourceRows = parsed.data.filter(row => {
                if (!row.time) return false;
                const d = new Date(row.time);
                return d.getTime() > cutoff;
            });

            let processedData = [];

            if (isComparative) {
                // PIVOT logic for overlaying multiple devices
                // Group by timestamp (rounded to nearest 5 seconds to align slightly offset logs)
                const groups = new Map();
                
                sourceRows.forEach(row => {
                    const d = new Date(row.time);
                    // Snap to 5s window to group near-simultaneous sensor logs
                    const tsKey = Math.floor(d.getTime() / 5000) * 5000; 
                    const devId = row['device_id'] || row['device_name'] || 'unknown';
                    const devShort = (devId.includes('0x')) ? devId.split('_').pop() : devId;

                    if (!groups.has(tsKey)) {
                        groups.set(tsKey, { 
                            time: row.time,
                            displayTime: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        });
                    }
                    
                    const entry = groups.get(tsKey);
                    // Add sensor values with device prefix
                    dataKeys.forEach(k => {
                        if (row[k] !== undefined) {
                            entry[`${devShort}_${k}`] = row[k];
                        }
                    });
                });

                processedData = Array.from(groups.values()).sort((a, b) => new Date(a.time) - new Date(b.time));
            } else {
                // LEGACY Filter logic
                let rows = sourceRows;
                if (filter) {
                    rows = rows.filter(row => {
                        return Object.entries(filter).every(([key, value]) => {
                            const rowVal = row[key] !== undefined ? row[key] : row['device_id'] !== undefined ? row['device_id'] : row['device_name'];
                            if (typeof rowVal === 'string' && typeof value === 'string') {
                                return rowVal.toLowerCase() === value.toLowerCase();
                            }
                            return rowVal === value;
                        });
                    });
                }

                processedData = rows.map(row => ({
                    ...row,
                    displayTime: row.time ? new Date(row.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
                }));
            }

            setData(processedData);
            setError(null);
        } catch (err) {
            console.error(`[TelemetryChart] ${filename} error:`, err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filename, filter, dataKeys, isComparative, historyHours]);

    useEffect(() => {
        pullData();
        const interval = setInterval(pullData, refreshInterval);
        return () => clearInterval(interval);
    }, [pullData, refreshInterval]);

    // Generate accurate data keys for comparative mode
    // e.g. if we have 0x48 and 0x4b, and keys v0,v1... we want 0x48_v0, 0x4b_v0
    const linesToRender = useMemo(() => {
        if (!isComparative) return dataKeys.map((k, i) => ({ key: k, color: colors[i % colors.length], label: k.toUpperCase() }));

        // For comparative, we need to inspect the data or know the devices
        // We'll extract all keys that look like DEVICE_KEY
        if (data.length === 0) return [];
        
        const allKeys = Object.keys(data[0]).filter(k => k !== 'time' && k !== 'displayTime');
        return allKeys.map((k, i) => ({
            key: k,
            color: colors[i % colors.length],
            label: k.replace('_', ' ').toUpperCase()
        }));
    }, [isComparative, dataKeys, colors, data]);

    if (error && data.length === 0) {
        return (
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-red)' }}>
                <p>⚠️ Failed to load {title} history</p>
                {deviceTag && <p style={{ fontSize: '0.65rem' }}>Target: {deviceTag}</p>}
                <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>{error}</p>
            </div>
        );
    }

    return (
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', minHeight: '340px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>📈 {title}</h3>
                    {deviceTag && (
                        <span style={{ 
                            fontSize: '0.6rem', 
                            background: 'rgba(255,255,255,0.1)', 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            fontFamily: 'monospace',
                            color: 'var(--text-secondary)'
                        }}>
                            {deviceTag}
                        </span>
                    )}
                    {isComparative && (
                        <span style={{ 
                            fontSize: '0.6rem', 
                            background: 'var(--accent-blue)', 
                            color: 'white',
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            textTransform: 'uppercase'
                        }}>
                            Overlay
                        </span>
                    )}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    {data.length} PTS • {historyHours}H
                </div>
            </div>

            <div style={{ width: '100%', height: '220px', marginTop: '1rem' }}>
                {loading && data.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        Building Matrix View...
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis 
                                dataKey="displayTime" 
                                stroke="var(--text-secondary)" 
                                fontSize={10} 
                                tickLine={false} 
                                axisLine={false}
                                minTickGap={30}
                            />
                            <YAxis 
                                stroke="var(--text-secondary)" 
                                fontSize={10} 
                                tickLine={false} 
                                axisLine={false}
                                domain={['auto', 'auto']}
                            />
                            <Tooltip 
                                contentStyle={{ background: 'rgba(20,20,25,0.9)', border: '1px solid var(--glass-border)', borderRadius: '8px', fontSize: '12px' }}
                                itemStyle={{ padding: '2px 0' }}
                            />
                            <Legend 
                                onClick={toggleLine}
                                style={{ cursor: 'pointer' }}
                                wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} 
                            />
                            {linesToRender.map((line) => (
                                <Line
                                    key={line.key}
                                    name={line.label}
                                    type="monotone"
                                    dataKey={line.key}
                                    stroke={line.color}
                                    strokeWidth={2}
                                    dot={false}
                                    hide={hiddenKeys.includes(line.key)}
                                    connectNulls={true}
                                    activeDot={{ r: 4, stroke: 'white', strokeWidth: 2 }}
                                    animationDuration={500}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
            {isComparative && hiddenKeys.length > 0 && (
                <div style={{ fontSize: '0.65rem', color: 'var(--accent-blue)', opacity: 0.8, textAlign: 'center', marginTop: '0.4rem' }}>
                    💡 {hiddenKeys.length} sensor(s) hidden. Click legend to restore.
                </div>
            )}
        </div>
    );
}

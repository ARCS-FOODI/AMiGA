# Hardware Data Flow & Telemetry

This diagram outlines the detailed lifecycle of a sensor reading—from the moment physical soil voltage is captured to when it's rendered as an interactive chart on the frontend.

## Data Pipelining Sequence

```mermaid
sequenceDiagram
    participant Probes as Physical Probes
    participant ADS1115 as ADC (ADS1115)
    participant Reader as Backend Sensor Daemon
    participant EventBus as Dispatcher
    participant CSV as Active Session CSV
    participant FastAPI as Backend API
    participant React as Frontend UI

    %% Real-time Loop Phase
    loop Every 1 - 10 Seconds
        Probes->>ADS1115: Analog Voltage Change
        ADS1115-->>Reader: Digital Read (I2C)
        Reader->>EventBus: Broadcast Metric Data (Internal)
        EventBus->>CSV: Append Line (Time, ID, V0-V3)
    end

    %% Client Polling Phase
    loop Every 5 Seconds (Frontend Jitter Poll)
        React->>FastAPI: GET /active/window/sensors.csv
        FastAPI->>CSV: Stream Reverse Chronological Hours
        CSV-->>FastAPI: Raw High-Resolution Telemetry
        Note over FastAPI: Data Downsampling Process:<br/>Groups by ID, Max 150 points.<br/>Maintains Scale & Outline.
        FastAPI-->>React: Return Filtered JSON Payload
        React->>React: React 18 <br/> Background UI Render (Recharts)
    end
```

## Description of Stages

1.  **Analog Conversion (Hardware Limit)**: The physical probes measure resistance. The ADC board converts this to a digital voltage signal over I2C to the Raspberry Pi.
2.  **Continuous Polling (Local Logging)**: The robust local polling daemon continually attempts reading. If a read succeeds, it offloads to the asynchronous `EventBus` to ensure no IO blocking. 
3.  **Persistence**: The `EventBus` commits data to long-term `CSV` files immediately, providing maximum accuracy data-logging for science audits.
4.  **Optimized Retrieval (API Layer)**: Because the UI cannot handle translating potentially 100,000+ coordinates, the FastAPI backend processes the CSV when the UI poles for data. It calculates chronological bounding boxes and downsamples values using smart bucket strategies retaining only major feature points.
5.  **Non-Blocking UI Rendering**: React processes charting paths in background transitions causing zero lock-up or stutter on the main application interface despite rich visualization.

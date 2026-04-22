# High-Level System Architecture

This diagram illustrates the macro-level architecture of the AMiGA system, showing how the separate components interact across hardware and software boundaries.

## System Components

```mermaid
flowchart TD
    subgraph Web_Tier ["Frontend (React/Vite)"]
        UI_Dashboard["AMiGA Dashboard"]
        UI_Config["Recipe Configurator"]
        UI_Control["Manual Controls"]
        
        UI_Dashboard --> |WebSocket/HTTP| API_Gateway
        UI_Config --> |HTTP POST| API_Gateway
        UI_Control --> |HTTP POST| API_Gateway
    end
    
    subgraph Execution_Tier ["Backend Core (FastAPI)"]
        API_Gateway["FastAPI App Route Handlers"]
        Scheduler["Grow Scheduler (Daemon)"]
        State_Manager["Session State & Configs"]
        
        API_Gateway <--> State_Manager
        Scheduler <--> State_Manager
    end

    subgraph Hardware_Gateway ["Hardware Abstraction Layer"]
        Pump_Driver["Peristaltic Pumps (I2C)"]
        Light_Driver["SSR Relays (GPIO)"]
        Sensor_Driver["I2C/Modbus Bus"]
        
        API_Gateway --> Pump_Driver
        API_Gateway --> Light_Driver
        Scheduler --> Pump_Driver
        Scheduler --> Light_Driver
    end
    
    subgraph Data_Tier ["Persistence (CSV Logs)"]
        CSV_Env["Environmental Metrics (co2_data.csv)"]
        CSV_Soil["Analog Sensors (sensors.csv)"]
        CSV_Chem["Chemistry (sis_data.csv)"]
        
        Sensor_Driver -.-> |Logging Dispatcher| CSV_Env
        Sensor_Driver -.-> |Logging Dispatcher| CSV_Soil
        Sensor_Driver -.-> |Logging Dispatcher| CSV_Chem
        
        API_Gateway -.-> |Downsampled Reads| CSV_Env
        API_Gateway -.-> |Downsampled Reads| CSV_Soil
        API_Gateway -.-> |Downsampled Reads| CSV_Chem
    end

    subgraph Edge_Nodes ["Edge Devices"]
        Jetson["Jetson Orin\n(Dual Camera Vision/IR)"]
        Pi4["Pi4 Scraper\n(Vivosun Integration)"]
        
        Jetson -.-> |Image Save| Data_Tier
        Pi4 -.-> |Telemetry Scrape| API_Gateway
    end

    Hardware_Gateway <--> |Physical Wiring| physical_devices((Physical Grow Trays))
```

## Component Breakdown

1.  **Web Tier (Frontend)**: Responsible for visualization. The frontend actively queries the `API_Gateway` to render dynamic charts.
2.  **Execution Tier (Backend)**: The core brain running on a local Raspberry Pi/PC. Handles all business logic, routing, and automation (via the `Grow Scheduler`).
3.  **Hardware Gateway**: Contains specific Python driver code used to serialize signals over standard hardware interfaces.
4.  **Data Tier**: Represents the persistent local CSV files. We decouple high-frequency sensor writes from API reads utilizing a pub-sub data dispatcher layout.
5.  **Edge Nodes**: Auxiliary devices acting on the periphery of the main system, contributing to or fetching from the primary platform.

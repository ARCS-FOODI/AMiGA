# AMiGA Project Evolution Timeline

This storyboard documents the developmental timeline of the AMiGA project and traces how the hardware shifted to meet expanding semester requirements, mapping the journey from a basic localized microcontroller to a robust, networked IoT platform.

## 1. The Initial Setup (Pi 5 Iteration 1)
Our first major proof-of-concept operated entirely on a single **Raspberry Pi 5** focused on a standard 10x10 grow tray.

**Hardware & Features:**
- 4 Moisture Probes (one for each corner of the 10x10 tray).
- Dual Peristaltic Pump Setup (same hardware used today).
- Basic Camera Recording module.

**Software Architecture:**
- **No GUI / Dashboard**: The system was fully headless.
- **Simple Logic**: Irrigation was controlled exclusively by a simple, flat Python script running basic `IF threshold < limit THEN dispense` moisture logic.

## 2. Vivosun & Waydroid R&D (Pi 5 Iteration 2)
The next goal was to integrate the closed-source commercial **Vivosun Aero Lush** AC unit into the environment. 

**Development:**
- We successfully installed **Waydroid** on the Raspberry Pi 5.
- We developed the initial set of scripts and macro logic to automate the AC.
- **Architectural Note**: At this time, the Pi 5 was being accessed locally. Because of this, it natively ran **Wayland** (the default Pi 5 display server). Waydroid ran perfectly on Wayland without the need for complex VNC wrappers or X11 bridges.

## 3. The Kratky Interception (Mid-Semester Pivot)
Midway through development, a new project was introduced , Kratky Root Growth Project. This project required us to analyze plant root growth over extended multi-hour/daily timelines. 

**Hardware Shift:**
- The powerful Raspberry Pi 5 was extracted from the AMiGA setup and entirely transferred to the new **Kratky Root Growth Project**.

**Kratky Implementation:**
- To achieve the root growth analysis, we engineered a dedicated local video recording server.
- The Pi 5 now uses `OBS` to capture root growth streams and runs a robust `FFMPEG` local ingest server (`pi5_kratky/scripts/start_recording.sh`), compressing video into `x265` Ultra-Fast 1-frame-per-second (`-r 1`) `.mkv` files tailored explicitly for long-term timelapse analysis.

## 4. Physical Enclosure & Rapid Prototyping
As the interconnected hardware ecosystem expanded, the need for a rigorous environmental boundary became critical.
- **The Grow Tent**: The entire platform was deployed into a sealed `3ft x 3ft x 6ft` Vivosun Grow Tent to stabilize environmental variables.
- **The Wood Rig "Hack"**: Initial attempts to mount the increasingly heavy electronics alongside the liquid components using provided commercial styrofoam boards resulted in two structural collapses. In response, the team executed a rapid overnight build to construct a custom `2.5ft x 2.5ft x 3ft` tiered wooden tower. 
- **Wet/Dry Isolation**: This custom tiered approach allowed the physical isolation of "wet" components (10x10 trays, pumps, and inline moisture probes) on the upper levels, while securing the core Raspberry Pi controller safely on the bottom level, routing all power lines completely outside the tent.

## 5. Developer Onboarding & Simulation Ecosystem
As the team scaled alongside the hardware, standardizing the student software-development experience became paramount. To allow new associate developers to safely contribute without risking physical components, we introduced a robust onboarding and simulation pipeline.
- **Onboarding Infrastructure**: Created a comprehensive suite of initialization `/scripts/` to automate environment setup, alongside a rigorously detailed `README.md`. This streamlined the installation pipeline, ensuring new team members could immediately access the required packages and run the project locally.
- **Agentic Coding & Modern IDEs**: The team adopted modern development practices utilizing **Visual Studio Code** heavily augmented by **Antigravity** (Agentic AI). This empowered student developers to rapidly analyze the codebase, comprehend existing documentation, and confidently prototype features.
- **The Simulated Environment**: To protect the live experiment, developers deploy their features into a local software "Simulation" mode. This safe sandbox mirrors the physical hardware's behaviors and responses extensively, allowing students to test bold changes securely before smoothly translating verified code directly to the real system.
- **Networking & Remote Collaboration**: To support multiple developers working concurrently, we deployed a dedicated **GL-iNet AXT1800 Wi-Fi Router**, centralizing all project devices on a private local network for seamless file transfers. Students utilize **SSH** and **TigerVNC** for direct, full-control mobile development on the hardware. Additionally, we integrated **Tailscale**, providing secure, zero-config VPN access so off-site contributors can conveniently develop and merge code from home.

## 6. Current Architecture: AMiGA Reimagined (Pi 4 & Orin)
With the Pi 5 relocated to the Kratky module and the physical tent rig actively stabilizing the environment, the team rebuilt the core AMiGA software platform onto a **Raspberry Pi 4**, scaling it up drastically to support remote team development and advanced metrics.

**Hardware & Features:**
- Raspberry Pi 4 (Core Controller).
- Scaled from 4 sensor to 8-probe Arrays and Modbus SIS NPK sensors. 
- Integrated **Jetson Orin** for high-computation Vision pipelines and thermal imaging.
- **RJ11 Commercial Light Hack**: Spliced into the commercial grow-light's RJ11 controller cable and integrated a programmable relay switch. By programmatically shorting a specific pair of the 4 wires, we successfully reverse-engineered full automation of the closed-source lighting unit.

**Software Evolution:**
- **The Dashboard Phase**: Transitioned from a simple flat Python script into a robust multi-tiered application featuring a **React.js Frontend** and a **FastAPI Python Backend**.
- **The Vivosun / X11 Innovation**: Because the Pi 4 was accessed remotely by multiple off-site developers, the system *mandated* **TigerVNC**, which only runs on the **X11** Display Server. 
- Since Waydroid only runs on Wayland, the original Pi 5 Vivosun logic failed. To overcome this, the team engineered the innovative **Weston X11-Backend Bridge**, allowing the Android emulator and Vivosun macros to successfully run nested inside the legacy X11 environment, completing the architecture we run today.

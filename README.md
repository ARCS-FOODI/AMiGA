# 🌿 AMiGA: Automated Modular Irrigation & Growth Assistant

**A research prototype developed under the FOODI (Facilitating Overcoming Obstacles to the Development and Integration of Modern Technologies for Controlled Environment Agriculture)** initiative at the **Autonomy Research Center for STEAHM (ARCS), California State University, Northridge**.

---

## 📖 Overview

The **AMiGA System** is part of a broader research effort within the **FOODI project**, a NASA-affiliated initiative led by the **Autonomy Research Center for STEAHM (ARCS)**.  
The project’s mission is to **facilitate the development, integration, and adoption of modern technologies** that strengthen the field of **Controlled Environment Agriculture (CEA)** — an approach to food production that leverages technology to sustainably manage light, temperature, humidity, and water use for optimal plant growth.

Within this framework, AMiGA serves as a **proof-of-concept platform** for automation, environmental sensing, and sustainable irrigation practices. It represents one of several experimental systems designed to demonstrate how **accessible, modular technology** can be applied to real-world agricultural challenges.

---

## 🌎 About FOODI

**FOODI** — _Facilitating Overcoming Obstacles to the Development and Integration of Modern Technologies for Controlled Environment Agriculture_ — is a multidisciplinary research program based at **ARCS, California State University, Northridge (CSUN)**.

The initiative addresses key barriers that limit the scalability and success of CEA systems, including:

- High infrastructure and energy costs
- Limited technical literacy and workforce readiness
- Challenges integrating diverse sensors and automation technologies
- Difficulty achieving consistent system performance across scales

To overcome these challenges, FOODI combines **academic research, industry collaboration, and hands-on student innovation** to prototype new technologies and processes that make CEA more efficient, reliable, and affordable.

---

## 🎯 Mission and Goals

FOODI’s long-term goal is to **empower the next generation of researchers and engineers** to advance sustainable agriculture through technology.  
Its objectives include:

- Developing **modular, scalable systems** that can adapt to different cultivation environments
- Promoting **data-driven decision-making** in water and nutrient management
- Strengthening **education and interdisciplinary collaboration** between engineering, agriculture, and environmental science
- Building partnerships that bridge **academia, industry, and government research**

AMiGA contributes to this mission by exemplifying how open-source tools, sensor feedback, and intelligent automation can support **precision irrigation** and **environmental control** within research and learning environments.

---

## 💡 Research Integration

The AMiGA project demonstrates FOODI’s principles in practice by focusing on:

- **Automation and feedback control** – using environmental data to drive resource-efficient irrigation
- **Interdisciplinary design** – integrating hardware, software, and agricultural expertise
- **Education and accessibility** – making advanced CEA research tools open and reproducible for student and institutional use
- **Sustainability and scalability** – supporting methods that reduce waste, conserve water, and improve reliability in food production systems

Together, these efforts help strengthen CEA’s potential as a viable, sustainable solution for future food systems — from laboratory prototypes to operational facilities.

---

## 🔗 Learn More

To learn more about the FOODI initiative and related research efforts, visit:  
👉 [ARCS FOODI Project Overview](https://arcs.center/facilitating-overcoming-obstacles-to-development-and-integration-foodi-of-modern-technologies-for-controlled-environment-agriculture-cea/)

---

## 🏗️ Repository Structure

The AMiGA software stack is modular, consisting of a separate backend and frontend:

- **`backend/`**: A **FastAPI** (Python 3.10+) application that handles hardware integration, sensor data logging, environmental control logic, and serves a REST API.
- **`frontend/`**: A **React** single-page application built with **Vite** (Node.js 20+) to provide a modern, responsive user dashboard for monitoring and controlling the system.

Both components can be run in **Simulation Mode** (mocking hardware) for development or **Native Mode** for execution on a Raspberry Pi.

---

## 🚀 Setup & Running Instructions

AMiGA provides automated setup scripts to configure the Python virtual environment and install Node.js dependencies.

### Prerequisites

- **Python 3.10+**
- **Node.js 20+**

### Windows

Run the provided batch script to set up both the backend and frontend:

```cmd
install_dependencies.bat
```

### Linux (Debian/Ubuntu) & Raspberry Pi OS

Run the bash script to configure the environment:

```bash
./install_dependencies.sh
```

### macOS

The automated setup script (`.sh`) uses `apt-get` and is tailored for Debian-based systems. For macOS, please set up the repository manually:

1. Create a Python virtual environment: `python3 -m venv .venv` and activate it: `source .venv/bin/activate`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Navigate to the frontend directory: `cd frontend`
4. Install Node.js dependencies: `npm install`

---

### 🏃‍♂️ Running the System

#### Simulation Mode (Development)

If you are developing on a PC/Mac without Raspberry Pi hardware, you can run the system in simulation mode. This mocks the GPIO and sensor readings.

- **Windows**: `start_simulate.bat`
- **Linux / macOS**: `./start_simulate.sh`

These scripts will start both the FastAPI backend (on port 8000) and the Vite frontend (on port 5173).

#### Native Environment (Production)

For running AMiGA on an actual Raspberry Pi connected to real sensors and pumps:

- **Linux / Raspberry Pi OS**: `./start.sh`

_(Note: There is no Windows script for native execution since it requires Raspberry Pi GPIO pins.)_

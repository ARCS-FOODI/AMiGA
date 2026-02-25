---
description: Test the Dashboard (Simulation Mode)
---
This workflow automatically starts both the FastAPI backend (in simulation mode) and the Vite React frontend in a single terminal.

It uses the `start_simulate.sh` script to run both servers concurrently and gracefully kill them both when you press `Ctrl+C`.

// turbo-all
1. Start the AMiGA software stack
```bash
./start_simulate.sh
```

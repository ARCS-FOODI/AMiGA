import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import LightControl from './components/LightControl'
import PumpControl from './components/PumpControl'
import SensorMonitor from './components/SensorMonitor'
import SISMonitor from './components/SISMonitor'
import AutomationRules from './components/AutomationRules'
import ScaleMonitor from './components/ScaleMonitor'

function App() {
  return (
    <>
      <Header />

      <main className="grid-layout">
        <LightControl />
        <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
        <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
        <SISMonitor title="Main Grow Area SIS" />
        <SensorMonitor title="Tray 1 Sensors" addr={0x48} />
        <SensorMonitor title="Tray 2 Sensors" addr={0x49} />
        <ScaleMonitor />
        <AutomationRules />
      </main>
    </>
  )
}

export default App

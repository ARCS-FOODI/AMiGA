import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import LightControl from './components/LightControl'
import PumpControl from './components/PumpControl'
import SensorMonitor from './components/SensorMonitor'
import AutomationRules from './components/AutomationRules'
import ScaleMonitor from './components/ScaleMonitor'
import SevenInOneSensor from './components/SevenInOneSensor'

function App() {
  return (
    <>
      <Header />

      <main className="grid-layout">
        <LightControl />
        <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
        <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
        <SensorMonitor title="Tray 1 Sensors" addr={0x48} doPin={6} />
        <SensorMonitor title="Tray 2 Sensors" addr={0x49} doPin={24} />
        <SevenInOneSensor />
        <ScaleMonitor />
        <AutomationRules />
      </main>
    </>
  )
}

export default App

import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import LightControl from './components/LightControl'
import PumpControl from './components/PumpControl'
import SensorMonitor from './components/SensorMonitor'
import AutomationRules from './components/AutomationRules'

function App() {
  return (
    <>
      <Header />

      <main className="grid-layout">
        <LightControl />
        <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
        <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
        <SensorMonitor />
        <AutomationRules />
      </main>
    </>
  )
}

export default App

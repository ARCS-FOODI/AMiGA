import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import LightControl from './components/LightControl'
import PumpEmergencyControl from './components/PumpEmergencyControl'
import PumpControl from './components/PumpControl'
import SensorMonitor from './components/SensorMonitor'
import SISMonitor from './components/SISMonitor'
import SCD41Monitor from './components/SCD41Monitor'
import TSL2561Monitor from './components/TSL2561Monitor'
import AutomationRules from './components/AutomationRules'
import ScaleMonitor from './components/ScaleMonitor'
import RecordingButton from './components/RecordingButton'

function App() {
  return (
    <>
      <Header />

      <main className="grid-layout">
        <PumpEmergencyControl />
        <LightControl />
        <RecordingButton />
        <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
        <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
        <SISMonitor title="Main Grow Area SIS" />
        <SCD41Monitor title="Environmental Condition (SCD41)" />
        <TSL2561Monitor title="Luminosity (TSL2561)" />
        <SensorMonitor title="Tray 1 Sensors" addr={0x48} />
        <SensorMonitor title="Tray 2 Sensors" addr={0x4B} />
        <ScaleMonitor />
        <AutomationRules />
      </main>
    </>
  )
}

export default App

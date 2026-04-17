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
import RecipeManager from './components/RecipeManager'
import GrowthControlCenter from './components/GrowthControlCenter'
import ScaleMonitor from './components/ScaleMonitor'
import RecordingButton from './components/RecordingButton'

function App() {
  return (
    <>
      <Header />

      <main className="main-content">
        <section className="category-section">
          <h2 className="category-header">System & Automation</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <GrowthControlCenter />
            <RecordingButton />
            <RecipeManager />
          </div>
        </section>

        <section className="category-section">
          <h2 className="category-header">Actuators & Controls</h2>
          <div className="grid-layout">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', gridColumn: 'span 2' }}>
              <PumpEmergencyControl />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
                <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
                <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
              </div>
            </div>
            <LightControl />
          </div>
        </section>

        <section className="category-section">
          <h2 className="category-header">Environment Monitors</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <SCD41Monitor title="Environmental Condition (SCD41)" />
            <TSL2561Monitor title="Luminosity (TSL2561)" />
          </div>
        </section>

        <section className="category-section">
          <h2 className="category-header">Grow Trays & Payload</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <SISMonitor title="Main Grow Area SIS" />
            <div className="grid-layout">
              <SensorMonitor title="Tray 1 Sensors" addr={0x48} />
              <SensorMonitor title="Tray 2 Sensors" addr={0x4B} />
              <ScaleMonitor />
            </div>
          </div>
        </section>
      </main>
    </>
  )
}

export default App

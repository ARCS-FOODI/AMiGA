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
import TelemetryChart from './components/TelemetryChart'
import DiagnosticConsole from './components/DiagnosticConsole'

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
            <div className="grid-layout">
              <TelemetryChart 
                title="Air Quality History (SCD41)" 
                filename="co2_data.csv" 
                dataKeys={["co2_ppm", "humidity_percent", "temperature_c"]} 
                colors={["var(--accent-teal)", "var(--accent-blue)", "var(--accent-orange)"]}
              />
              <TelemetryChart 
                title="Luminosity History (TSL2561)" 
                filename="light_data.csv" 
                dataKeys={["lux"]} 
                colors={["var(--accent-yellow)"]}
              />
            </div>
            <SCD41Monitor title="Environmental Condition (SCD41)" />
            <TSL2561Monitor title="Luminosity (TSL2561)" />
          </div>
        </section>

        <section className="category-section">
          <h2 className="category-header">Grow Trays & Payload</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <TelemetryChart 
                title="Comparative Moisture History (Matrix)" 
                filename="sensors.csv" 
                isComparative={true}
                dataKeys={["v0", "v1", "v2", "v3"]} 
                colors={[
                  "var(--accent-teal)", "var(--accent-green)", "var(--accent-blue)", "var(--accent-purple)",
                  "var(--accent-orange)", "var(--accent-yellow)", "#f43f5e", "#d946ef"
                ]}
              />
            </div>
            <div className="grid-layout">
              <TelemetryChart 
                title="Soil Nutrients (SIS NPK)" 
                filename="sis_data.csv" 
                dataKeys={["nitrogen", "phosphorus", "potassium"]} 
                colors={["var(--accent-purple)", "var(--accent-orange)", "var(--accent-yellow)"]}
              />
              <TelemetryChart 
                title="Soil Chemistry (SIS)" 
                filename="sis_data.csv" 
                dataKeys={["ph", "ec", "temperature"]} 
                colors={["var(--accent-green)", "var(--accent-blue)", "var(--accent-red)"]}
              />
              <TelemetryChart 
                title="Moisture History (Tray 1)" 
                filename="sensors.csv" 
                filter={{ device_id: 'ADS1115_0x48' }}
                dataKeys={["v0", "v1", "v2", "v3"]} 
                colors={["var(--accent-teal)", "var(--accent-green)", "var(--accent-blue)", "var(--accent-purple)"]}
              />
              <TelemetryChart 
                title="Moisture History (Tray 2)" 
                filename="sensors.csv" 
                filter={{ device_id: 'ADS1115_0x4b' }}
                dataKeys={["v0", "v1", "v2", "v3"]} 
                colors={["var(--accent-teal)", "var(--accent-green)", "var(--accent-blue)", "var(--accent-purple)"]}
              />
              <TelemetryChart 
                title="Weight History (Scale)" 
                filename="scale_data.csv" 
                dataKeys={["weight_g"]} 
                colors={["var(--accent-orange)"]}
              />
            </div>
            <SISMonitor title="Main Grow Area SIS" />
            <div className="grid-layout">
              <SensorMonitor title="Tray 1 Sensors" addr={0x48} />
              <SensorMonitor title="Tray 2 Sensors" addr={0x4B} />
              <ScaleMonitor />
            </div>
          </div>
        </section>
      </main>

      {/* Floating System Diagnostic Terminal */}
      <DiagnosticConsole />
    </>
  )
}

export default App

import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import LightControl from './components/LightControl'
import PumpControl from './components/PumpControl'
import SensorMonitor from './components/SensorMonitor'
<<<<<<< HEAD
import AutomationRules from './components/AutomationRules'
import ScaleMonitor from './components/ScaleMonitor'
=======
import SoilSensor7in1 from './components/SoilSensor7in1'
import AutomationRules from './components/AutomationRules'
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)

function App() {
  return (
    <>
      <Header />

      <main className="grid-layout">
        <LightControl />
        <PumpControl pumpName="water" colorBase="var(--accent-blue)" hoverBase="#3b82f6" />
        <PumpControl pumpName="food" colorBase="var(--accent-green)" hoverBase="#10b981" />
        <SensorMonitor />
<<<<<<< HEAD
        <ScaleMonitor />
=======
        <SoilSensor7in1 />
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)
        <AutomationRules />
      </main>
    </>
  )
}

export default App

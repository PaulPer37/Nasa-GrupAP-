import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { GeoCodingService } from './services/GeoCodingAPI'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <GeoCodingService/>
    </>
  )
}

export default App

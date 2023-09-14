import ReactGA from 'react-ga'
import { BrowserRouter } from "react-router-dom"
import './App.css'
import NavBar from './routes/NavBar'
import Routing from "./routes/Routing"
import { useEffect } from 'react'

function App() {

  return (
    <>
      <BrowserRouter>
        <NavBar />
        <Routing />
      </BrowserRouter>
    </>
  )
}

export default App


import { Route, Routes } from "react-router-dom"
import Home from "../views/Races"
import Races from "../views/Races"
import Bets from "../views/Bets"

function Routing() {
    return (
        <div>
            <Routes>
                <Route path="races" element={<Races />} />
                <Route path="bets" element={<Bets />} />
                <Route path="/" element={<Races />} />
            </Routes>
        </div>
    )
}

export default Routing
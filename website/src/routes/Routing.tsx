
import { Route, Routes } from "react-router-dom"
import Orders from "../views/Orders"
import Races from "../views/Races"
import Strategy from "../views/Strategy"
import Admin from "../views/admin"

function Routing() {
    return (
        <div>
            <Routes>
                <Route path="races" element={<Races />} />
                <Route path="orders" element={<Orders />} />
                <Route path="strategyeditor" element={<Strategy />} />
                <Route path="/" element={<Races />} />
                <Route path="/admin" element={<Admin />} />
            </Routes>
        </div>
    )
}

export default Routing
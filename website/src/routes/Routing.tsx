
import { Route, Routes } from "react-router-dom"
import Home from "../views/Races"
import Races from "../views/Races"
import Orders from "../views/Orders"

function Routing() {
    return (
        <div>
            <Routes>
                <Route path="races" element={<Races />} />
                <Route path="orders" element={<Orders />} />
                <Route path="/" element={<Races />} />
            </Routes>
        </div>
    )
}

export default Routing
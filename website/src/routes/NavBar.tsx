import 'bootstrap/dist/css/bootstrap.css';
import { Link } from "react-router-dom";

function NavBar() {
    return (
        <nav className="navbar navbar-expand-sm fixed-top navbar-light bg-light">
            <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarTogglerDemo03" aria-controls="navbarTogglerDemo03" aria-expanded="false" aria-label="Toggle navigation">
                <span className="navbar-toggler-icon"></span>
            </button>
            <a className="navbar-brand" href="/">sickpunt</a>

            <div className="collapse navbar-collapse" id="navbarTogglerDemo03">
                <ul className="navbar-nav mr-auto">
                    <li className="nav-item">
                    <   Link className="nav-link" to="/races">Races</Link>
                    </li>
                    <li className="nav-item">
                        <Link className="nav-link" to="/bets">Bets</Link>
                    </li>
                </ul>
            </div>
        </nav>
    )
}

export default NavBar
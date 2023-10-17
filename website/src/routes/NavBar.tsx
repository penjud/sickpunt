import React, { useState } from "react";
import 'bootstrap/dist/css/bootstrap.css';
import { Link } from "react-router-dom";

function NavBar() {
  const [isOpen, setIsOpen] = useState(false);

  const toggle = () => setIsOpen(!isOpen);

  return (
    <nav className="navbar navbar-expand-sm fixed-top navbar-light bg-light">
      <button className="navbar-toggler" type="button" onClick={toggle} aria-label="Toggle navigation">
        <span className="navbar-toggler-icon"></span>
      </button>
      <a className="navbar-brand" href="/">sickpunt</a>

      <div className={`collapse navbar-collapse ${isOpen ? 'show' : ''}`} id="navbarTogglerDemo03">
        <ul className="navbar-nav mr-auto">
          <li className="nav-item">
            <Link className="nav-link" to="/races">Races</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/orders">Orders</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/strategyeditor">Strategies</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/admin">Admin</Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default NavBar;

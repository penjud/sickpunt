import { useEffect, useState } from 'react';
import { API_URL } from '../helper/Constants';
import './Strategy.css';
import TimeBeforeRaceSlider from './TimeBeforeRaceSlider';


function Strategy() {
  // State for each form element
  const [strategyName, setStrategyName] = useState("");
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedSportType, setSelectedSportType] = useState("");
  const [betType, setBetType] = useState(""); // "Lay" or "Back"

  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");


  const [strategies, setStrategies] = useState([]);
  const [currentStrategy, setCurrentStrategy] = useState(null);

  const [isActiveSpeedMap, setIsActiveSpeedMap] = useState(false);
  const [isActiveFluctuations, setIsActiveFluctuations] = useState(false);

  useEffect(() => {
    // Fetch available strategies when the component mounts
    fetch(`http://${API_URL}/get_strategies`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        setAvailableStrategies(data.strategies || []); // assuming the response contains an array named 'strategies'
      })
      .catch(error => console.error('Error fetching strategies:', error));
  }, []);


  const loadStrategy = () => {
    fetch(`http://${API_URL}/load_strategy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: selectedStrategy })
    })
      .then(res => res.json())
      .then(data => {
        // Update state based on the returned strategy data
        setStrategyName(data.strategyName);
        setSelectedCountries(data.selectedCountries);
        setSelectedSportType(data.selectedSportType);
        setBetType(data.betType);
        // ... and other necessary state updates
      })
      .catch(error => console.error('Error loading strategy:', error));
  };

  // Render
  return (
    <div className="strategy-form">
      <h2>Strategy Editor</h2>

      {/* Load existing strategy */}
      <div className="load-strategy">
        <label>Select Strategy:</label>
        <select value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)}>
          {availableStrategies.map(strategy => (
            <option key={strategy} value={strategy}>{strategy}</option>
          ))}
        </select>
        <button onClick={loadStrategy}>Load</button>
      </div>

      {/* Strategy Name */}
      <div className="strategy-name">
        <label>Strategy Name:</label>
        <input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} />
      </div>

      {/* Country Selection */}
      <div className="country-selection">
        <label>Select Countries:</label>
        <select multiple value={selectedCountries} onChange={(e) => setSelectedCountries(Array.from(e.target.selectedOptions, option => option.value))}>
          <option value="AU">Australia</option>
          <option value="NZ">New Zealand</option>
          <option value="GB">Great Britain</option>
          <option value="IRE">Ireland</option>
          <option value="FRA">France</option>
          <option value="USA">USA</option>
        </select>
      </div>

      {/* Sport Type Selection */}
      <div className="sport-type">
        <label>Select Sport Type:</label>
        <select value={selectedSportType} onChange={(e) => setSelectedSportType(e.target.value)}>
          <option value="Horse Racing">Horse Racing</option>
          {/* ... add other sport types */}
        </select>
      </div>

      {/* Bet Type */}
      <div className="bet-type">
        <label>Bet Type:</label>
        <label>
          <input type="radio" value="Lay" checked={betType === "Lay"} onChange={() => setBetType("Lay")} />
          Lay
        </label>
        <label>
          <input type="radio" value="Back" checked={betType === "Back"} onChange={() => setBetType("Back")} />
          Back
        </label>
      </div>

      <div>
        <TimeBeforeRaceSlider />
      </div>


      <div className="row">
        <div className="col-md-6">
          {/* SpeedMapOptions Component */}
          <div className="mb-3">
            <label>Speed Map Options:</label>
            <button onClick={() => setIsActiveSpeedMap(!isActiveSpeedMap)}>Toggle Activation</button>
            {/* Placeholder for SpeedMapOptions parameters */}
          </div>

          {/* FluctuationsOptions Component */}
          <div className="mb-3">
            <label>Fluctuations Options:</label>
            <button onClick={() => setIsActiveFluctuations(!isActiveFluctuations)}>Toggle Activation</button>
            {/* Placeholder for FluctuationsOptions parameters */}
          </div>

          {/* And similarly for other components... */}

        </div>

        <div className="col-md-6">
          {/* Right column for the corresponding parameters */}
          {isActiveSpeedMap && <div>SpeedMapOptions Parameters here</div>}
          {isActiveFluctuations && <div>FluctuationsOptions Parameters here</div>}
          {/* And similarly for other components... */}
        </div>
      </div>

      {/* ... other form elements ... */}

      {/* Submit button */}
      <div className="submit-btn">
        <button onClick={() => { /* TODO: Add logic to send data to API */ }}>Save Strategy</button>
      </div>
    </div>
  );
}

export default Strategy;

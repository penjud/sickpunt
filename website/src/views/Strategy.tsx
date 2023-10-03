import 'bootstrap/dist/css/bootstrap.css';
import { useEffect, useState } from 'react';
import Editor from '../components/StrategyEditor/Editor';
import { API_URL } from '../helper/Constants';
import './Strategy.css';
import TimeBeforeRaceSlider from './TimeBeforeRaceSlider';

interface IAttributesConfig {
  [key: string]: {
    min?: number,
    max?: number,
  } | string | undefined;
  StrategyName?: string;
}



function Strategy() {
  // State for each form element
  const [strategyName, setStrategyName] = useState<string>("");
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedSportType, setSelectedSportType] = useState("");
  const [betType, setBetType] = useState(""); // "Lay" or "Back"

  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [attributesConfig, setAttributesConfig] = useState<IAttributesConfig>({});

  const saveStrategy = () => {

    // Function to display Bootstrap alerts
    const displayAlert = (message, type) => {
      const alertDiv = document.createElement('div');
      alertDiv.className = `alert alert-${type} fixed-bottom text-center mb-0 rounded-0`;
      alertDiv.innerHTML = message;
      document.body.appendChild(alertDiv);
      setTimeout(() => alertDiv.remove(), 3000);
    };

    // Validation: Check if strategyName has at least 3 characters
    if (!strategyName || strategyName.length < 3) {
      displayAlert('Enter a strategy name under which to save the configuration', 'danger');
      return;
    }

    const payload = {
      strategyName,
      attributesConfig
    };

    // Log payload to the console
    console.log("Saving strategy with the following configuration:", payload);

    // Make POST request to /save_strategy
    fetch(`http://${API_URL}/save_strategy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
      .then(response => response.json())
      .then(data => {
        console.log("Response from server:", data);
        displayAlert('Strategy successfully saved', 'success');
      })
      .catch(error => {
        console.error("Error saving strategy:", error);
        displayAlert('Failed to save strategy', 'danger');
      });
  };


  useEffect(() => {
    // Fetch available strategies when the component mounts
    fetch(`http://${API_URL}/get_strategies`, { method: 'POST' })  // consider changing POST to GET
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
          {/* <option value="NZ">New Zealand</option>
          <option value="GB">Great Britain</option>
          <option value="US">USA</option> */}
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

      <div className="timeSlider">
        <TimeBeforeRaceSlider />
      </div>

      <div>
        <Editor attributesConfig={attributesConfig} setAttributesConfig={setAttributesConfig} />
      </div>

      {/* Submit button */}
      <div className="submit-btn">
        <button onClick={saveStrategy}>Save Strategy</button> {/* Invoke saveStrategy when clicked */}
      </div>
    </div>
  );
}

export default Strategy;

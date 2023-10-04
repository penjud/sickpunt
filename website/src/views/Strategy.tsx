import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.css';
import { useEffect, useState } from 'react';
import Editor from '../components/StrategyEditor/Editor';
import { API_URL, DATA_ATTRIBUTES } from '../helper/Constants';
import './Strategy.css';
import TimeBeforeRaceSlider from './TimeBeforeRaceSlider';

interface IAttributesConfig {
  active: string;
  StrategyName: string;
  selectedCountries: string[];
  selectedSportType: string;
  betType: string;
  betSize: number;
  priceStrategy: string;
  priceMinValue: number;
  priceMaxValue: number;
  maxHorsesToBet: number;
  maxHorsesToBetStrategy: string;
  minLayTotalOdds: number;
  maxLayTotalOdds: number;
  minBackTotalOdds: number;
  maxBackTotalOdds: number;
  minLastTotalOdds: number;
  maxLastTotalOdds: number;
}

const defaultAttributesConfig: IAttributesConfig = {
  active: "off",
  StrategyName: "",
  selectedCountries: [],
  selectedSportType: "Horse Racing",
  betType: "",
  betSize: 0,
  priceStrategy: "",
  priceMinValue: 0,
  priceMaxValue: 0,
  maxHorsesToBet: 0,
  maxHorsesToBetStrategy: "",
  minLayTotalOdds: 0,
  maxLayTotalOdds: 5,
  minBackTotalOdds: 0,
  maxBackTotalOdds: 5,
  minLastTotalOdds: 0,
  maxLastTotalOdds: 5,
};


function Strategy() {


  const [availableStrategies, setAvailableStrategies] = useState<string[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");
  const [data, setData] = useState<IAttributesConfig>(defaultAttributesConfig);


  // Function to display Bootstrap alerts
  const displayAlert = (message, type) => {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fixed-bottom text-center mb-0 rounded-0`;
    alertDiv.innerHTML = message;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
  };


  const updateAttributeConfig = (attr: string, newMin?: number, newMax?: number) => {
    // Clone the existing attributesConfig state
    const updatedAttributesConfig = { ...data };

    // Update the specific attribute's min and max values
    updatedAttributesConfig[attr] = {
      min: newMin !== undefined ? newMin : data[attr]?.min,
      max: newMax !== undefined ? newMax : data[attr]?.max,
    };

    // Update the state
    setData(updatedAttributesConfig);
  };

  const saveStrategy = () => {



    // Validation: Check if strategyName has at least 3 characters
    if (!data.StrategyName) {
      displayAlert('Enter a strategy name under which to save the configuration', 'danger');
      return;
    }

    for (const attr of DATA_ATTRIBUTES) {
      if (data.hasOwnProperty(attr)) {
        if (data[attr]?.min === undefined || data[attr]?.max === undefined) {
          displayAlert(`Please set both minimum and maximum for ${attr}`, 'danger');
          return;
        }
      }
    }

    // Additional Validation: Either Lay or Back should be selected
    if (!data.betType) {
      displayAlert('Please select either Lay or Back', 'danger');
      return;
    }

    // Validation: Check if at least one country is selected
    if (!data.SelectedCountries || data.SelectedCountries.length === 0) {
      displayAlert('At least one country must be selected', 'danger');
      return;
    }

    // Validation: Check if at least one sport type is selected
    if (!data.selectedSportType || data.selectedSportType === "") {
      displayAlert('At least one sport type must be selected', 'danger');
      return;
    }

    // Additional Validation: Either Lay or Back should be selected
    if (data.betSize < 1) {
      displayAlert('Please select a bet size', 'danger');
      return;
    }

    // Additional Validation: A min and a max price need to be entered
    if (data.priceMinValue < 1 || data.priceMaxValue < 1) {
      displayAlert('Please enter both a minimum and a maximum price', 'danger');
      return;
    }

    // Log payload to the console
    console.log("Saving strategy with the following configuration:", data);

    // Make POST request to /save_strategy
    axios.post(`http://${API_URL}/save_strategy`, { strategy_config: data })
      .then(response => {
        console.log("Response from server:", response.data);
        displayAlert('Strategy successfully saved', 'success');
      })
      .catch(error => {
        console.error("Error saving strategy:", error);
        displayAlert('Failed to save strategy', 'danger');
      });
  };


  useEffect(() => {
    axios.post(`http://${API_URL}/get_strategies`)
      .then(res => {
        setAvailableStrategies(res.data.strategies || []);
        console.log('Available Strategies:', res.data.strategies);
        setData(defaultAttributesConfig);
      })
      .catch(error => {
        console.error('Error fetching strategies:', error);
      });
  }, []);



  const loadStrategy = () => {
    console.log("Loading Strategy:", selectedStrategy);  // Debug log

    // Initialize data with defaultAttributesConfig
    setData(defaultAttributesConfig);
    console.log("data before loading:", data)

    axios.post(`http://${API_URL}/load_strategy`, null, { params: { strategy_name: selectedStrategy } })
      .then(res => {
        // Merge the default attributes with the loaded strategy data
        const mergedData = { ...defaultAttributesConfig, ...res.data };

        // Update the state to re-render your component
        setData(mergedData);
        displayAlert('Strategy loaded', 'success');
      })
      .catch(error => {
        console.error('Error loading strategy:', error);
        displayAlert('Failed to load strategy', 'danger');
      });
  };


  const handleChange = (attr: keyof IAttributesConfig, value: any) => {
    setData(prevConfig => ({ ...prevConfig, [attr]: value }));
  };

  // Render
  return (
    <div className="strategy-form">
      <h2>Strategy Editor</h2>

      {/* Load existing strategy */}
      <div className="selections-box">
        <label>Select Strategy:</label>
        <div className="selections">
          <select value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)}>
            <option value="" disabled>Select a strategy</option> {/* This option is added */}
            {availableStrategies.map(strategy => (
              <option key={strategy} value={strategy}>{strategy}</option>
            ))}
          </select>
          <button onClick={loadStrategy}>Load</button>
        </div>
      </div>


      {/* Strategy Name */}
      <div className="strategy-name">
        <label>Strategy Name:</label>
        <input type="text" value={data.StrategyName} onChange={(e) => handleChange('StrategyName', e.target.value)} />
      </div>

      {/* Price and min/max values */}
      <div className="selection-box d-flex">
        <label>Strategy status:</label>
        <div className="selections">
          <select value={data.active} onChange={(e) => handleChange('active', e.target.value)}>
            <option value="">Select</option>
            <option value="off">Deactivated</option>
            <option value="dummy">Dummy</option>
            <option value="on">Active</option>
          </select>
        </div>
      </div>

      {/* Country Selection */}
      <div className="country-selection">
        <label>Select Countries:</label>
        <select multiple value={data.SelectedCountries} onChange={(e) => handleChange('SelectedCountries', Array.from(e.target.selectedOptions, option => option.value))}>
          <option value="AU">Australia</option>
          <option value="NZ">New Zealand</option>
          <option value="GB">Great Britain</option>
          <option value="US">USA</option>
        </select>
      </div>

      {/* Sport Type Selection */}
      <div className="sport-type">
        <label>Select Sport Type:</label>
        <select value={data.selectedSportType} onChange={(e) => handleChange('selectedSportType', e.target.value)}>
          <option value="">Select</option>
          <option value="Horse Racing">Horse Racing</option>
          {/* ... add other sport types */}
        </select>
      </div>

      {/* Bet Type */}
      <div className="selection-box centered">
        <label>Bet Type:</label>
        <div className="radio-boxes">
          <label>
            <input type="radio" value="Lay" checked={data.betType === "Lay"} onChange={() => handleChange('betType', "Lay")} />
            Lay
          </label>
          <label>
            <input type="radio" value="Back" checked={data.betType === "Back"} onChange={() => handleChange('betType', "Back")} />
            Back
          </label>
        </div>
      </div>

      {/* Bet Size */}
      <div className="bet-size">
        <label>Bet Size:</label>
        <input type="number" value={data.betSize} onChange={(e) => handleChange('betSize', parseFloat(e.target.value))} />
      </div>

      {/* Price and min/max values */}
      <div className="selection-box d-flex">
        <label>Price:</label>
        <div className="selections">
          <select value={data.priceStrategy} onChange={(e) => handleChange('priceStrategy', e.target.value)}>
            <option value="back">current Back</option>
            <option value="last">Last traded</option>
            <option value="lay">current Lay</option>
            <option value="_back_moving_avg">Back moving average</option>
            <option value="_lay_moving_avg">Lay moving average</option>
          </select>
          <input type="number" placeholder="Min" value={data.priceMinValue} onChange={(e) => handleChange('priceMinValue', e.target.value)} />
          <input type="number" placeholder="Max" value={data.priceMaxValue} onChange={(e) => handleChange('priceMaxValue', e.target.value)} />
        </div>
      </div>


      {/* Multi horses */}
      <div className="selection-box d-flex">
        <label>Maximum different horses bet per race</label>
        <div className="selections">
          <input type="number" placeholder="Max" value={data.maxHorsesToBet} onChange={(e) => handleChange('maxHorsesToBet', e.target.value)} />

          <select value={data.maxHorsesToBetStrategy} onChange={(e) => handleChange('maxHorsesToBetStrategy', e.target.value)}>
            <option value="lowest odds first">Lowest odds first</option>
            <option value="highest odds first">Highest odds first</option>
          </select>
        </div>
      </div>


      {/* Multi horses */}
      <div className="selection-box d-flex">
        <label>Sum of odds in race</label>
        <div className="selections">
          <label>Back</label>
          <input type="number" value={data.minBackTotalOdds} onChange={(e) => handleChange('minBackTotalOdds', e.target.value)} />
          <input type="number" value={data.maxBackTotalOdds} onChange={(e) => handleChange('maxBackTotalOdds', e.target.value)} />
        </div>
        <div className="selections">
          <label>Lay</label>
          <input type="number" value={data.minLayTotalOdds} onChange={(e) => handleChange('minLayTotalOdds', e.target.value)} />
          <input type="number" value={data.maxLayTotalOdds} onChange={(e) => handleChange('maxLayTotalOdds', e.target.value)} />
        </div>
        <div className="selections">
          <label>Last</label>
          <input type="number" value={data.minLastTotalOdds} onChange={(e) => handleChange('minLastTotalOdds', e.target.value)} />
          <input type="number" value={data.maxLastTotalOdds} onChange={(e) => handleChange('maxLastTotalOdds', e.target.value)} />
        </div>
      </div>

      <div className="timeSlider centered">
        <TimeBeforeRaceSlider attributesConfig={data} handleChange={handleChange} />
      </div>

      <div>
        <Editor attributesConfig={data} setAttributesConfig={setData} updateAttributeConfig={updateAttributeConfig} />
      </div>

      {/* Submit button */}
      <div className="submit-btn">
        <button onClick={saveStrategy}>Save Strategy</button> {/* Invoke saveStrategy when clicked */}
      </div>
    </div>
  );
}

export default Strategy;

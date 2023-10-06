import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.css';
import { useEffect, useState } from 'react';
import { API_URL } from '../helper/Constants';
import './Strategy.css';


interface IAttributesConfig {
  active: string;
  StrategyName: string;
}

const defaultAttributesConfig: IAttributesConfig = {
  active: "off",
  StrategyName: "",
};


function Admin() {
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


  const updateData = (attr: string, newMin?: number, newMax?: number) => {
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

  const saveAdmin = () => {
    // Validation: Check if strategyName has at least 3 characters
    if (!data.StrategyName) {
      displayAlert('Enter a strategy name under which to save the configuration', 'danger');
      return;
    }

    // Additional Validation: A min and a max price need to be entered
    if (data.priceMinValue < 1 || data.priceMaxValue < 1) {
      displayAlert('Please enter both a minimum and a maximum price', 'danger');
      return;
    }

    // Log payload to the console
    console.log("Saving strategy with the following configuration:", data);

    // Make POST request to /save
    axios.post(`http://${API_URL}/save_admin`, { strategy_config: data })
      .then(response => {
        console.log("Response from server:", response.data);
        displayAlert('Strategy successfully saved', 'success');
      })
      .catch(error => {
        console.error("Error saving strategy:", error);
        displayAlert('Failed to save strategy', 'danger');
      });
  };


  const loadAdmin = () => {
    console.log("Loading Strategy:", selectedStrategy);  // Debug log

    // Initialize data with defaultAttributesConfig
    setData(defaultAttributesConfig);
    console.log("data before loading:", data)

    axios.post(`http://${API_URL}/load_admin`, null, { params: { strategy_name: selectedStrategy } })
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
      <h2>Admin</h2>


      {/* Strategy Name */}
      <div className="strategy-name">
        <label>Mongodb IP</label>
        <input type="text" value={data.StrategyName} onChange={(e) => handleChange('StrategyName', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Login</label>
        <input type="text" value={data.StrategyName} onChange={(e) => handleChange('StrategyName', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Password</label>
        <input type="text" value={data.StrategyName} onChange={(e) => handleChange('StrategyName', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Token</label>
        <input type="text" value={data.StrategyName} onChange={(e) => handleChange('StrategyName', e.target.value)} />
      </div>


      {/* Country Selection */}
      <div className="country-selection">
        <label>Countries to stream data from:</label>
        <select multiple value={data.selectedCountries} onChange={(e) => handleChange('selectedCountries', Array.from(e.target.selectedOptions, option => option.value))}>
          <option value="AU">Australia</option>
          <option value="NZ">New Zealand</option>
          <option value="GB">Great Britain</option>
          <option value="IE">Ireland</option>
          <option value="US">USA</option>
        </select>
      </div>


      {/* Submit button */}
      <div className="submit-btn">
        <button onClick={saveAdmin}>Save</button> {/* Invoke saveStrategy when clicked */}
      </div>
    </div>
  );
}

export default Admin;

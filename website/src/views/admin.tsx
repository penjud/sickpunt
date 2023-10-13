import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.css';
import { useEffect, useState } from 'react';
import { API_URL } from '../helper/Constants';
import './Strategy.css';


interface IAttributesConfig {
  UserName: string;
}

const defaultAttributesConfig: IAttributesConfig = {
  UserName: "default",
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
    if (!data.UserName) {
      displayAlert('Enter a strategy name under which to save the configuration', 'danger');
      return;
    }

    // Additional Validation: A min and a max price need to be entered
    if (data.priceMinValue < 1 || data.priceMaxValue < 1) {
      displayAlert('Please enter both a minimum and a maximum price', 'danger');
      return;
    }

    // Log payload to the console
    // console.log("Saving strategy with the following configuration:", data);

    // Make POST request to /save
    axios.post(`http://${API_URL}/save_admin`, { admin_dict: data })
      .then(response => {
        console.log("Response from server:", response.data);
        displayAlert('Saved successfully', 'success');
      })
      .catch(error => {
        console.error("Error saving Admin:", error);
        displayAlert('Failed to save', 'danger');
      });
  };


  const loadAdmin = () => {

    // Initialize data with defaultAttributesConfig
    setData(defaultAttributesConfig);
    console.log("data before loading:", data)

    axios.post(`http://${API_URL}/load_admin`, null)
      .then(res => {
        // Merge the default attributes with the loaded strategy data
        const mergedData = { ...defaultAttributesConfig, ...res.data };

        // Update the state to re-render your component
        setData(mergedData);
        console.log(mergedData);
        displayAlert('Admin loaded', 'success');
      })
      .catch(error => {
        console.error('Error loading admin:', error);
        displayAlert('Failed to load admin', 'danger');
      });
  };

  // Load data on startup of page mount
  useEffect(() => {
    loadAdmin();
  }, []);




  const handleChange = (attr: keyof IAttributesConfig, value: any) => {
    setData(prevConfig => ({ ...prevConfig, [attr]: value }));
  };

  // Render
  return (
    <div className="strategy-form">
      <h2>Admin</h2>

      <div className="strategy-name">
        <label>Usernamne</label>
        <input type="text" value={data.Email} onChange={(e) => handleChange('Email', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Passwword</label>
        <input type="password" value={data.UserPassword} onChange={(e) => handleChange('UserPassword', e.target.value)} />
      </div>
      <div className="strategy-name">
        <label>Server Address</label>
        <input type="text" value={data.ServerAddress} onChange={(e) => handleChange('ServerAddress', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Login</label>
        <input type="text" value={data.BetfairLogin} onChange={(e) => handleChange('BetfairLogin', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Password</label>
        <input type="password" value={data.BetfairPassword} onChange={(e) => handleChange('BetfairPassword', e.target.value)} />
      </div>

      <div className="strategy-name">
        <label>Betfair Token</label>
        <input type="password" value={data.BetfairToken} onChange={(e) => handleChange('BetfairToken', e.target.value)} />
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
        <button onClick={saveAdmin}>Save</button> 
      </div>
    </div>
  );
}

export default Admin;

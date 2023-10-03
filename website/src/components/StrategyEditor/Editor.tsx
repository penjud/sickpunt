import 'bootstrap/dist/css/bootstrap.css';
import { useState } from 'react';


const DATA_ATTRIBUTES = [
  "Avg $",
  "Bar",
  "Career",
  "Last 10",
  "Number",
  "Odds",
  "P%",
  "Rtg",
  "W%",
  "Wgt",
  "Age",
  "Apprentice",
  "Average Prize Money",
  "Barrier",
  "Best Fixed Odds",
  "BetEasy Odds",
  "Career Place Strike Rate",
  "Career Placings",
  "Career Prize Money",
  "Career ROI",
  "Career Runs",
  "Career Strike Rate",
  "Career Wins",
  "Dry Track ROI",
  "Dry Track Runs",
  "Dry Track Strike Rate",
  "Dry Track Wins",
  "Finish Result (Updates after race)",
  "Gender",
  "Handicap Rating",
  "Jockey",
  "Jockey 12 Month Avg Horse Earnings",
  "Jockey 12 Month Horse Earnings",
  "Jockey 12 Months Place Strike Rate",
  "Jockey 12 Months Places",
  "Jockey 12 Months ROI",
  "Jockey 12 Months Starts",
  "Jockey 12 Months Strike Rate",
  "Jockey 12 Months Wins",
  "Jockey Last 100 Avg Horse Earnings",
  "Jockey Last 100 Horse Earnings",
  "Jockey Last 100 Place Strike Rate",
  "Jockey Last 100 Places",
  "Jockey Last 100 ROI",
  "Jockey Last 100 Starts",
  "Jockey Last 100 Strike Rate",
  "Jockey Last 100 Wins",
  "Jockey Last Season Avg Horse Earnings",
  "Jockey Last Season Horse Earnings",
  "Jockey Last Season Place Strike Rate",
  "Jockey Last Season Places",
  "Jockey Last Season ROI",
  "Jockey Last Season Starts",
  "Jockey Last Season Strike Rate",
  "Jockey Last Season Wins",
  "Jockey This Season Avg Horse Earnings",
  "Jockey This Season Horse Earnings",
  "Jockey This Season Place Strike Rate",
  "Jockey This Season Places",
  "Jockey This Season ROI",
  "Jockey This Season Starts",
  "Jockey This Season Strike Rate",
  "Jockey This Season Wins",
  "Jockey Weight Claim",
  "Last Start Distance",
  "Last Start Distance Change",
  "Last Start Finish Position",
  "Last Start Margin",
  "Last Start Prize Money",
  "Num",
  "Prize Money",
  "This Condition Place Strike Rate",
  "This Condition Places",
  "This Condition ROI",
  "This Condition Runs",
  "This Condition Strike Rate",
  "This Condition Wins",
  "This Distance Place Strike Rate",
  "This Distance Places",
  "This Distance ROI",
  "This Distance Runs",
  "This Distance Strike Rate",
  "This Distance Wins",
  "This Track Distance Place Strike Rate",
  "This Track Distance Places",
  "This Track Distance ROI",
  "This Track Distance Runs",
  "This Track Distance Strike Rate",
  "This Track Distance Wins",
  "This Track Place Strike Rate",
  "This Track Places",
  "This Track ROI",
  "This Track Runs",
  "This Track Strike Rate",
  "This Track Wins",
  "Trainer",
  "Trainer 12 Month Avg Horse Earnings",
  "Trainer 12 Month Horse Earnings",
  "Trainer 12 Months Place Strike Rate",
  "Trainer 12 Months Places",
  "Trainer 12 Months ROI",
  "Trainer 12 Months Starts",
  "Trainer 12 Months Strike Rate",
  "Trainer 12 Months Wins",
  "Trainer Last 100 Avg Horse Earnings",
  "Trainer Last 100 Horse Earnings",
  "Trainer Last 100 Place Strike Rate",
  "Trainer Last 100 Places",
  "Trainer Last 100 ROI",
  "Trainer Last 100 Starts",
  "Trainer Last 100 Strike Rate",
  "Trainer Last 100 Wins",
  "Trainer Last Season Avg Horse Earnings",
  "Trainer Last Season Horse Earnings",
  "Trainer Last Season Place Strike Rate",
  "Trainer Last Season Places",
  "Trainer Last Season ROI",
  "Trainer Last Season Starts",
  "Trainer Last Season Strike Rate",
  "Trainer Last Season Wins",
  "Trainer This Season Avg Horse Earnings",
  "Trainer This Season Horse Earnings",
  "Trainer This Season Place Strike Rate",
  "Trainer This Season Places",
  "Trainer This Season ROI",
  "Trainer This Season Starts",
  "Trainer This Season Strike Rate",
  "Trainer This Season Wins",
  "Weight",
  "Weight Carried",
  "Wet Track ROI",
  "Wet Track Runs",
  "Wet Track Strike Rate",
  "Wet Track Wins"
];


const Editor = ({ attributesConfig, setAttributesConfig }) => {
  const [selectedAttributes, setSelectedAttributes] = useState([]);
  const [selectedDropDownValue, setSelectedDropDownValue] = useState('');

  const addAttribute = () => {
    if (selectedDropDownValue && !selectedAttributes.includes(selectedDropDownValue)) {
      setSelectedAttributes([...selectedAttributes, selectedDropDownValue]);
      setAttributesConfig({ ...attributesConfig, [selectedDropDownValue]: {} });
      console.log(attributesConfig);
    }
  };

  const updateAttributeConfig = (attr: string, newMin?: number, newMax?: number) => {
    // Clone the existing attributesConfig state
    const updatedAttributesConfig = { ...attributesConfig };

    // Update the specific attribute's min and max values
    updatedAttributesConfig[attr] = {
      min: newMin !== undefined ? newMin : attributesConfig[attr]?.min,
      max: newMax !== undefined ? newMax : attributesConfig[attr]?.max,
    };

    // Update the state
    setAttributesConfig(updatedAttributesConfig);
  };

  const removeAttribute = (attr: string) => {
    setSelectedAttributes(selectedAttributes.filter(a => a !== attr));
  };

  return (
    <div className="container">
      <div className="row">
        <h3>Attribute Selection</h3>
        <div className="col-8">
          <div style={{ position: 'relative' }}> {/* Container for select and icon */}
            <select id="attribute-dropdown" className="form-control" style={{ paddingRight: '24px' }} value={selectedDropDownValue} onChange={(e) => setSelectedDropDownValue(e.target.value)}>
              <option value="" disabled>Select attribute</option>
              {DATA_ATTRIBUTES.map(attr => (
                <option key={attr} value={attr}>{attr}</option>
              ))}
            </select>
            <div style={{ position: 'absolute', top: '50%', right: '8px', pointerEvents: 'none', transform: 'translateY(-50%)' }}>
              <i className="fas fa-chevron-down"></i> {/* FontAwesome Down Arrow */}
            </div>
          </div>
        </div>
        <div className="col-4">
          <button className="btn btn-primary" onClick={addAttribute}>Add</button>
        </div>
      </div>
      <div>
        <h3>Selected Attributes</h3>
        <div>All the following elements need to be met for a bet to bet placed</div>
        <ul>
          {selectedAttributes.map(attr => (
            <li key={attr} className="row">
              <div className="col-4">{attr}</div>
              <div className="col-3">
                Min: <input className="form-control" type="number" onChange={(e) => updateAttributeConfig(attr, e.target.value, attributesConfig[attr]?.max)} />
              </div>
              <div className="col-3">
                Max: <input className="form-control" type="number" onChange={(e) => updateAttributeConfig(attr, attributesConfig[attr]?.min, e.target.value)} />
              </div>
              <div className="col-2">
                <button className="btn btn-danger" onClick={() => removeAttribute(attr)}>Remove</button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Editor;

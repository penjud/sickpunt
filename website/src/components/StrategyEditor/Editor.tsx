import 'bootstrap/dist/css/bootstrap.css';
import { useEffect, useState } from 'react';
import { DATA_ATTRIBUTES } from '../../helper/Constants';
import '../../views/Strategy.css';



const Editor = ({ attributesConfig, setAttributesConfig, updateAttributeConfig }) => {
  const [selectedAttributes, setSelectedAttributes] = useState([]);
  const [selectedDropDownValue, setSelectedDropDownValue] = useState('');

  // Keep selectedAttributes in sync with attributesConfig
  useEffect(() => {
    const attributes = Object.keys(attributesConfig).filter(attr => DATA_ATTRIBUTES.includes(attr));
    setSelectedAttributes(attributes);
    console.log(attributesConfig)
  }, [attributesConfig]);


  const addAttribute = () => {
    if (selectedDropDownValue && !selectedAttributes.includes(selectedDropDownValue)) {
      // setSelectedAttributes([...selectedAttributes, selectedDropDownValue]);
      setAttributesConfig({ ...attributesConfig, [selectedDropDownValue]: {} });
      console.log(attributesConfig);
    }
  };



  const removeAttribute = (attr: string) => {
    // setSelectedAttributes(selectedAttributes.filter(a => a !== attr));
    const updatedAttributesConfig = { ...attributesConfig };
    delete updatedAttributesConfig[attr];
    setAttributesConfig(updatedAttributesConfig);
  };

  return (
    <div className="container">
      <div className="row">
        <h3>Available conditions</h3>
        <div className="col-8">
          <div> {/* Container for select and icon */}
            <select id="attribute-dropdown" className="form-control" style={{ paddingRight: '24px' }} value={selectedDropDownValue} onChange={(e) => setSelectedDropDownValue(e.target.value)}>
              <option value="" disabled>Select attribute</option>
              {DATA_ATTRIBUTES.map(attr => (
                <option key={attr} value={attr}>{attr}</option>
              ))}
            </select>
            <div>
              <i className="fas fa-chevron-down"></i> {/* FontAwesome Down Arrow */}
            </div>
          </div>
        </div>
        <div className="col-4">
          <button className="btn btn-primary" onClick={addAttribute}>Add</button>
        </div>
      </div>
      <div>
        <h3>Selected Conditions</h3>
        <div>All the following elements need to be met for a bet to bet placed</div>
        <ul>
          {selectedAttributes.map(attr => (
            <li key={attr} className="row align-items-center">
              <div className="col-4">{attr}</div>
              <div className="col-3">
                Min: <input className="form-control" type="number" value={attributesConfig[attr]?.min || ""} onChange={(e) => updateAttributeConfig(attr, e.target.value, attributesConfig[attr]?.max)} />
              </div>
              <div className="col-3">
                Max: <input className="form-control" type="number" value={attributesConfig[attr]?.max || ""} onChange={(e) => updateAttributeConfig(attr, attributesConfig[attr]?.min, e.target.value)} />
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

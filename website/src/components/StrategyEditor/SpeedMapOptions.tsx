import React from 'react';

function SpeedMapOptions({ isActive }) {
  if (!isActive) return null;

  return (
    <div>
      <h3>Speed Map Options</h3>
      <div>
        <label>Early (Barrier) choices:</label>
        <select>
          {/* ... Add your options here */}
        </select>
      </div>
      <div>
        <label>Settling Position choices:</label>
        <select>
          {/* ... Add your options here */}
        </select>
      </div>
      <div>
        <label>Closing Speed choices:</label>
        <select>
          {/* ... Add your options here */}
        </select>
      </div>
    </div>
  );
}

export default SpeedMapOptions;

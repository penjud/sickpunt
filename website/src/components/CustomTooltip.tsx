import React from 'react';

export const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload[0]?.payload.data) {
    const selectedData = payload[0].payload.data;

    // Create an array of 30-row chunks
    const horseInfoEntries = Object.entries(selectedData._horse_info);
    const chunks = [];
    let i, j, chunk = 30;
    for (i = 0, j = horseInfoEntries.length; i < j; i += chunk) {
      chunks.push(horseInfoEntries.slice(i, i + chunk));
    }

    return (
      <div className="custom-tooltip">
        <div className="info-section">
          <div>{`Horse Name: ${selectedData._horse_name}`}</div>
          <div>{`Last Min: ${(1 / selectedData._last_min)?.toFixed(2)}`}</div>
          <div>{`Last: ${(1 / selectedData.last)?.toFixed(2)}`}</div>
          <div>{`Last Max: ${(1 / selectedData._last_max)?.toFixed(2)}`}</div>
        </div>
        
        <div className="table-section">
          {selectedData._horse_info && (
            chunks.map((chunk, index) => (
              <table key={index} className="tooltip-table">
                {chunk.map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{value}</td>
                  </tr>
                ))}
              </table>
            ))
          )}
        </div>
      </div>
    );
  }
  return null;
};

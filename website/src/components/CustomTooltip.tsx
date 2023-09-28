import React from 'react';

export const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload[0]?.payload.data) {
        const selectedData = payload[0].payload.data;

        return (
            <div className="custom-tooltip">
                <div>  {`Horse Name: ${selectedData._horse_name}`}</div>
                {/* <p className="intro">{`Horse ID: ${selectedData.horseId}`}</p> */}
                <div>  {`Last Min: ${(1 / selectedData._last_min)?.toFixed(2)}`}</div>
                <div> {`Last: ${(1 / selectedData.last)?.toFixed(2)}`}</div>
                <div> {`Last Max: ${(1 / selectedData._last_max)?.toFixed(2)}`}</div>

                {selectedData._horse_info && (
                    <table className="tooltip-table">
                        {Object.entries(selectedData._horse_info).map(([key, value]) => (
                            <tr key={key}>
                                <td>{key}</td>
                                <td>{value}</td>
                            </tr>
                        ))}
                    </table>
                )}
            </div>
        );
    }
    return null;
};

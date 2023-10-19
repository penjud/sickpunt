import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../helper/Constants';
import './Table.css';



function Funds() {
  const [balanceData, setBalanceData] = useState(null);

  useEffect(() => {
    async function fetchBalanceData() {
      try {
        const response = await axios.post(
          `http://${API_URL}/balance`,
          {},
          { headers: { 'Content-Type': 'application/json' } }
        );
        setBalanceData(response.data);
      } catch (error) {
        console.error('There was an error fetching the balance data:', error);
      }
    }

    fetchBalanceData();
  }, []);

  return (
    <div className="funds">
      {balanceData ? (
        <table border="1">
          <tbody>
            {Object.entries(balanceData).map(([key, value], index) => (
              <tr key={index}>
                <td>{key}</td>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default Funds;

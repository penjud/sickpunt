import React, { useEffect, useState } from 'react';
import axios from 'axios';
import PivotTableUI from 'react-pivottable/PivotTableUI';
import 'react-pivottable/pivottable.css';
import CircularProgress from '@mui/material/CircularProgress';
import { API_URL } from '../helper/Constants';
import './Table.css';

const PivotTable = ({ endpoint }) => {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [pivotState, setPivotState] = useState({});

  useEffect(() => {
    axios
      .post(`http://${API_URL}/${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      .then((response) => {
        setOrders(response.data);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching:', error);
      });
  }, []);

  return (
    <div className="pivot">
      {isLoading ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '50vh',
          }}
        >
          <CircularProgress />
        </div>
      ) : (
        <div>
          <PivotTableUI
            data={orders}
            onChange={(s) => setPivotState(s)}
            {...pivotState}
          />
        </div>
      )}
    </div>
  );
};

export default PivotTable;

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import 'react-tabulator/lib/styles.css';
import 'react-tabulator/css/tabulator.min.css';
import { ReactTabulator } from 'react-tabulator';
import CircularProgress from '@mui/material/CircularProgress';
import { API_URL } from '../helper/Constants';
import './Table.css';

const Table = ({ endpoint }: { endpoint: string }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    axios
      .post(`http://${API_URL}/${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      .then((response) => {
        setData(response.data);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching:', error);
      });
  }, [endpoint]);

  const nonEmptyColumns = data.length > 0 ? 
    Object.keys(data[0]).filter(key =>
      data.some(row => row[key] !== null && row[key] !== undefined)
    ) : [];

    const outcomeFormatter = (cell: any, formatterParams: any, onRendered: any) => {
      const value = cell.getValue();
      
      // Set the background color based on the value
      if (value === 'WON') {
        cell.getRow().getElement().style.backgroundColor = 'lightgreen';
      } else if (value === 'LOST') {
        cell.getRow().getElement().style.backgroundColor = 'pink'; // Using pink as a light red substitute
      }
    
      // Return the cell value so it gets displayed
      return value;
    };
    
    

  const columns = nonEmptyColumns.map((key) => ({
    title: key,
    field: key,
    sorter: 'string',
    headerFilter: 'input',
    formatter: key === 'bet_outcome' ? outcomeFormatter : null
  }));

  const options = {
    pagination: 'local',
    paginationSize: 30,
    layout: 'fitDataFill',
    initialSort: [
      { column: 'timestamp', dir: 'desc' }
    ],
    columnVertAlign: 'top',
    dataTree: true,
    dataTreeStartExpanded: false
  };

  return (
    <div className="table-wrapper">
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
        <ReactTabulator
          data={data}
          columns={columns}
          options={options}
        />
      )}
    </div>
  );
};

export default Table;

import React, { useEffect, useState } from 'react';
import '../App.css';
import OpenOrdersTable from '../components/OpenOrdersTable';
import { RaceChart } from '../components/RaceChart';
import { RaceData } from '../components/Types';

const MAX_RETRIES = 9999;
const API_URL = import.meta.env.VITE_REACT_APP_API_URL || '3.24.169.161:7777';

const DataStream2: React.FC = () => {
  const [raceData, setRaceData] = useState<RaceData[]>([]);
  let retryCount = 0;

  const connectSocket = () => {
    const socket = new WebSocket(`ws://${API_URL}/ff_cache`);

    socket.onmessage = (event) => {
      const rawData = JSON.parse(event.data);
      // console.log("WebSocket Data:", rawData);
      let formattedData: RaceData[] = Object.entries(rawData.ff_cache).map(([raceId, horses]) => {
        let horseData: HorseData[] = Object.entries(horses)
          .filter(([key]) => !key.startsWith('_'))
          .map(([horseId, data]) => ({
            horseId,
            data: {
              back: data.back,
              lay: data.lay,
              last: data.last,
              _back_overrun: data._back_overrun,
              _lay_overrun: data._lay_overrun,
              _back_moving_avg: data._back_moving_avg,
              _lay_moving_avg: data._lay_moving_avg,
              _last_moving_avg: data._last_moving_avg,
              _last_min: data._last_min,
              _last_max: data._last_max,
              _runner_name: data._runner_name,
              _horse_info: data._horse_info || {},
            },
          }));

        horseData = horseData.sort((a, b) => (1 / b.data.last) - (1 / a.data.last));

        return {
          raceId,
          horseData,
          overrunBack: horses._back_overrun,
          overrunLay: horses._lay_overrun,
          overrunLast: horses._last_overrun,
          secondsToStart: horses._seconds_to_start,
          orders: horses._orders,
        };
      });

      formattedData = formattedData.sort((a, b) => a.secondsToStart - b.secondsToStart);
      setRaceData(formattedData);
    };

    socket.onclose = (event) => {
      console.warn(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`);

      if (retryCount < MAX_RETRIES) {
        retryCount++;
        console.log(`Attempting to reconnect (${retryCount}/${MAX_RETRIES})...`);
        setTimeout(connectSocket, 2000);  // Attempt reconnect after 2 seconds
      } else {
        console.error('Maximum retry attempts reached. Please check the server or network.');
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket Error: ', error);
    };
  };

  useEffect(() => {
    const updateOnlineStatus = () => {
      console.log(navigator.onLine ? 'Online' : 'Offline');
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    connectSocket();  // Initiating WebSocket connection

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
    };
  }, []);

  return (
    <div>
      <div className="h1">Races</div>
      {raceData.map((race) => (
        <>
          <RaceChart
            key={race.raceId}
            raceId={race.raceId}
            horseData={race.horseData}
            overrunBack={race.overrunBack}
            overrunLay={race.overrunLay}
            overrunLast={race.overrunLast}
            secondsToStart={race.secondsToStart}
          />

          <OpenOrdersTable data={race.orders}/>
        </>

      ))}
    </div>
  );
};

export default DataStream2;

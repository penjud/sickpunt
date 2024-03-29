import { CircularProgress } from '@mui/material';
import React, { useEffect, useState } from 'react';
import '../App.css';
import Funds from '../components/Funds';
import OpenOrdersTable from '../components/OpenOrdersTable';
import { RaceChart } from '../components/RaceChart';
import { API_URL } from '../helper/Constants';
import { RaceData } from '../helper/Types';

const MAX_RETRIES = 999999;

const RaceStreamer: React.FC = () => {
  const [raceData, setRaceData] = useState<RaceData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastSortedTime, setLastSortedTime] = useState<number>(Date.now());


  let retryCount = 0;

  const stableSort = (arr) => {
    // Create an array of indices [0, 1, 2, ...]
    const indices = Array.from({ length: arr.length }, (_, i) => i);

    // Sort the indices array
    indices.sort((a, b) => {
        const diff = Math.abs(arr[a].secondsToStart - arr[b].secondsToStart);
        // Only sort if the difference is 30 or more
        if (diff >= 30) {
            return arr[a].secondsToStart - arr[b].secondsToStart;
        }
        // If the difference is less than 30, retain the original order
        return a - b;
    });

    // Create a new array in the sorted order
    return indices.map(index => arr[index]);
};
  

  useEffect(() => {
    const intervalId = setInterval(() => {
      setLastSortedTime(Date.now());
    }, 2000);

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (Date.now() - lastSortedTime >= 6000) {
        const sortedData = stableSort([...raceData]);
        setRaceData(sortedData);
    }
}, [lastSortedTime, raceData]);


  const connectSocket = () => {
    const socket = new WebSocket(`ws://${API_URL}/ff_cache`);

    socket.onmessage = (event) => {
      setIsLoading(false);
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
              _strategy_status: data._strategy_status || {},
            },
          }));

        horseData = horseData.sort((a, b) => (1 / b.data.last) - (1 / a.data.last));

        return {
          raceId,
          horseData,
          raceTitle: horses._race_title,
          overrunBack: horses._back_overrun,
          overrunLay: horses._lay_overrun,
          overrunLast: horses._last_overrun,
          secondsToStart: horses._seconds_to_start,
          orders: horses._orders,
          strategyStatus: horses._strategy_status,
        };
      });

      setLastSortedTime((prevLastSortedTime) => {
        const now = Date.now();
        if (now - lastSortedTime >= 2000) {
            const mergedData = [...raceData, ...formattedData];
            const sortedData = stableSort(mergedData);
            setRaceData(sortedData);
            setLastSortedTime(now);  // Update the last sorted time
        } else {
            const mergedData = [...raceData, ...formattedData];
            setRaceData(mergedData);
        }
        return prevLastSortedTime; // keep the lastSortedTime unchanged
    });


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
      <div className='fundsTable'>
        <Funds />
      </div>
      <div className="h1">Races</div>
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <CircularProgress />
        </div>
      ) : (
        raceData.map((race) => (
          <>
            <RaceChart
              key={race.raceId}
              raceId={race.raceId}
              raceTitle={race.raceTitle}
              horseData={race.horseData}
              overrunBack={race.overrunBack}
              overrunLay={race.overrunLay}
              overrunLast={race.overrunLast}
              secondsToStart={race.secondsToStart}
              strategyStatus={race.strategyStatus}
            />
            <OpenOrdersTable data={race.orders} />
          </>
        ))
      )}
    </div>
  );
};

export default RaceStreamer;

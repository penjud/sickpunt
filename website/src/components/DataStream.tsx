import React, { useEffect, useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts';

interface HorseData {
    horseId: string;
    data: {
        back: number;
        lay: number;
        last: number;
        _back_overrun: number;
        _lay_overrun: number;
        _back_moving_avg: number;
        _lay_moving_avg: number;
        _last_moving_avg: number;
        _last_min: number;
        _last_max: number;
        _runner_name: string;
        _horse_info: {
            'Horse Name': string;
            'Avg $': string;
            'Bar': string;
            'Career': string;
            'Last 10': string;
            'Number': string;
            'Odds': string;
            'P%': string;
            'Rtg': string;
            'W%': string;
            'Wgt': string;
        };
    }
}

interface RaceData {
    raceId: string;
    horseData: HorseData[];
    overrunBack: number;
    overrunLay: number;
    overrunLast: number;
    secondsToStart: number;
}

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload[0]?.payload.data) {
        const selectedData = payload[0].payload.data;

        return (
            <div className="custom-tooltip">
                <p className="intro">{`Horse Name: ${selectedData._horse_name}`}</p>
                {/* <p className="intro">{`Horse ID: ${selectedData.horseId}`}</p> */}
                <p className="intro">{`Last Min: ${(1 / selectedData._last_min)?.toFixed(2)}`}</p>
                <p className="intro">{`Last: ${(1 / selectedData.last)?.toFixed(2)}`}</p>
                <p className="intro">{`Last Max: ${(1 / selectedData._last_max)?.toFixed(2)}`}</p>
                
                {selectedData._horse_info && (
                    <table border="1">
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


const RaceChart: React.FC<RaceProps> = ({ raceId, horseData, overrunBack, overrunLay, overrunLast, secondsToStart }) => {
    const [linesVisibility, setLinesVisibility] = useState({
        back: true,
        backMovingAvg: false,
        lay: true,
        layMovingAvg: false,
        last: true,
        lastMovingAvg: false,
        lastMin: false,
        lastMax: false,
    });

    const toggleLineVisibility = (lineName: any) => {
        setLinesVisibility({
            ...linesVisibility,
            [lineName]: !linesVisibility[lineName],
        });
    };

    function OverrunComponent({ overrunBack, overrunLay, overrunLast }) {
        const [isHighlighted, setIsHighlighted] = useState(false);

        useEffect(() => {
            let timer;

            if (overrunLay > 1 || overrunBack < 1) {
                setIsHighlighted(true);
                timer = setTimeout(() => {
                    setIsHighlighted(false);
                }, 1000);
            }

            return () => {
                if (timer) {
                    clearTimeout(timer);
                }
            };
        }, [overrunLay]);

        return (
            <p style={{ background: isHighlighted ? 'red' : 'transparent' }}>
                Overruns (bk/ly/lt) {overrunBack.toFixed(2)}
                /{overrunLay.toFixed(2)}
                / {overrunLast.toFixed(2)}
            </p>
        );
    }



    const horseDataWithOdds = horseData.map((horse) => ({
        horseId: horse.horseId,
        data: {
            back: horse.data.back ? 1 / horse.data.back : null,
            lay: horse.data.lay ? 1 / horse.data.lay : null,
            last: horse.data.last ? 1 / horse.data.last : null,
            _back_overrun: horse.data._back_overrun,
            _lay_overrun: horse.data._lay_overrun,
            _back_moving_avg: horse.data._back_moving_avg ? 1 / horse.data._back_moving_avg : null,
            _lay_moving_avg: horse.data._lay_moving_avg ? 1 / horse.data._lay_moving_avg : null,
            _last_moving_avg: horse.data._last_moving_avg ? 1 / horse.data._last_moving_avg : null,
            _last_min: horse.data._last_min ? 1 / horse.data._last_min : null,
            _last_max: horse.data._last_max ? 1 / horse.data._last_max : null,
            _horse_name: horse.data._runner_name,
            _horse_info: horse.data._horse_info,
        },
    }));


    const chartHeight = 400;

    return (
        <div>
            <h2>Race {raceId}</h2>
            <OverrunComponent overrunBack={overrunBack} overrunLay={overrunLay} overrunLast={overrunLast} />
            <p>Seconds to start: {secondsToStart.toFixed(0)}</p>
            <div>
                <input type="checkbox" id="back" checked={linesVisibility.back} onChange={() => toggleLineVisibility('back')} />
                <label htmlFor="back">Back</label>

                <input type="checkbox" id="backMovingAvg" checked={linesVisibility.backMovingAvg} onChange={() => toggleLineVisibility('backMovingAvg')} />
                <label htmlFor="backMovingAvg">Back Moving Average</label>

                <input type="checkbox" id="lay" checked={linesVisibility.lay} onChange={() => toggleLineVisibility('lay')} />
                <label htmlFor="lay">Lay</label>

                <input type="checkbox" id="layMovingAvg" checked={linesVisibility.layMovingAvg} onChange={() => toggleLineVisibility('layMovingAvg')} />
                <label htmlFor="layMovingAvg">Lay Moving Average</label>

                <input type="checkbox" id="last" checked={linesVisibility.last} onChange={() => toggleLineVisibility('last')} />
                <label htmlFor="last">Last</label>

                <input type="checkbox" id="lastMovingAvg" checked={linesVisibility.lastMovingAvg} onChange={() => toggleLineVisibility('lastMovingAvg')} />
                <label htmlFor="lastMovingAvg">Last Moving Average</label>

                <input type="checkbox" id="lastMin" checked={linesVisibility.lastMin} onChange={() => toggleLineVisibility('lastMin')} />
                <label htmlFor="lastMin">Last Min</label>

                <input type="checkbox" id="lastMax" checked={linesVisibility.lastMax} onChange={() => toggleLineVisibility('lastMax')} />
                <label htmlFor="lastMax">Last Max</label>
            </div>

            <LineChart width={800} height={chartHeight} data={horseDataWithOdds}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                    dataKey="horseId"
                    angle={-90}
                    textAnchor="end"
                    interval={0}
                    height={150}
                    style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                    }}
                />
                <YAxis domain={[0, 1]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {linesVisibility.back && <Line type="monotone" dataKey="data.back" stroke="#8884d8" dot={{ r: 4 }} />}
                {linesVisibility.backMovingAvg && <Line type="monotone" dataKey="data._back_moving_avg" stroke="#8884d8" strokeDasharray="5 5" />}
                {linesVisibility.lay && <Line type="monotone" dataKey="data.lay" stroke="#82ca9d" dot={{ r: 4 }} />}
                {linesVisibility.layMovingAvg && <Line type="monotone" dataKey="data._lay_moving_avg" stroke="#82ca9d" strokeDasharray="5 5" />}
                {linesVisibility.last && <Line type="monotone" dataKey="data.last" stroke="#ffc658" dot={{ r: 4 }} />}
                {linesVisibility.lastMovingAvg && <Line type="monotone" dataKey="data._last_moving_avg" stroke="#ffc658" strokeDasharray="5 5" />}
                {linesVisibility.lastMin && <Line type="monotone" dataKey="data._last_min" stroke="#ff0000" dot={{ r: 4 }} />}
                {linesVisibility.lastMax && <Line type="monotone" dataKey="data._last_max" stroke="#00ff00" dot={{ r: 4 }} />}

            </LineChart>
        </div>
    );
};
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
            <h1>Races</h1>
            {raceData.map((race) => (
                <RaceChart
                    key={race.raceId}
                    raceId={race.raceId}
                    horseData={race.horseData}
                    overrunBack={race.overrunBack}
                    overrunLay={race.overrunLay}
                    overrunLast={race.overrunLast}
                    secondsToStart={race.secondsToStart}
                />
            ))}
        </div>
    );
};

export default DataStream2;
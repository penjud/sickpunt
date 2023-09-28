export interface HorseData {
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

export interface RaceData {
    raceId: string;
    horseData: HorseData[];
    overrunBack: number;
    overrunLay: number;
    overrunLast: number;
    secondsToStart: number;
}

export interface RaceProps {
    raceId: string;
    horseData: HorseData[];
    overrunBack: number;
    overrunLay: number;
    overrunLast: number;
    secondsToStart: number;
}
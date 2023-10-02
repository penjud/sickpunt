import React, { useState } from 'react';
import Slider from '@mui/material/Slider';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';


function TimeBeforeRaceSlider() {
    const [value, setValue] = useState([-3600, 600]);
  
    const handleChange = (event, newValue) => {
      setValue(newValue);
    };
  
    return (
      <Box sx={{ width: 500 }}>
        <Typography id="range-slider" gutterBottom>
          Place bets in this time window
        </Typography>
        <Slider
          value={value}
          onChange={handleChange}
          valueLabelDisplay="auto"
          aria-labelledby="range-slider"
          min={-3600}
          max={600}
          marks={[
            { value: -3600, label: '-3600s' },
            { value: 0, label: '0s' },
            { value: 600, label: '600s' }
          ]}
        />
        <div>
          From: {value[0]} seconds to {value[1]} seconds relative to start of race.
        </div>
      </Box>
    );
  }
  
  export default TimeBeforeRaceSlider;
  
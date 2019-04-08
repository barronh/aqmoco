Title: Air Quality Model Observation Comparison Operator (AQMOCO)
Author: Barron H. Henderson
Date: 2019-04-09

# OVERVIEW

The Air Quality Model Observation Comparison Operator uses observation
file inputs (csv) and air quality model outputs (PseudoNetCDF compatible)
to create NetCDF files that are spatially and temporally aligned using
missing data where an observation is not available. (dims: time, lay, site)

1. Extract model quantities at observation locations.
2. Average model quantities
3. Calculate derived model variables for comparison to observations
4. Calculate derived observation variables for comparison to models
5. Save results as NetCDF

# PREREQUISITES

* OS : Linux, Mac OS, Windows
* Python>=3.6
  * numpy>=1.2
  * pandas>=0.13
  * PseudoNetCDF>=3.0.1
  * pyproj

# CONTENTS

```
.
|-- README.md
|-- run.sh
|-- modinput
|   |-- COMBINE_ACONC_v53_intel18.0_2016_CONUS_201607.nc # example model file
|   `-- COMBINE_ACONC_v53_intel18.0_2016_CONUS_201608.nc # example day 2
|-- obsinput/
|   |-- AQS_full_site_list.csv # example meta data
|   `-- AQS_daily_data_2016.csv # example obs data
|-- defn
|   |-- moddefns.txt
|   |-- modsimple.txt
|   |-- obsdefn.txt
|   `-- obssimple.txt
|-- scripts
|   `-- modatobs.py
|-- output
    |-- modatobs.nc
    `-- obs.nc
```

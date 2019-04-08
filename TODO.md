# OVERVIEW

List of functionalities that should be added.

v0.02
-----
1. Extend to more networks or input files
2. Add timezone correction option
2. Automatically identify format/network being supplied for observations
3. Add typical definitions for CMAQ/CAMx and GEOS-Chem
4. Add mechanism for definitions to be maintained by user community

v0.01
-----
1. Reads AQS meta-data
2. Reads AQS observations
3. Pairs AQS meta-data and observations
4. Extracts CMAQ at AQS (proxy for PseudoNetCDF funcionality; no IOAPI specific)
5. Adds continuous time dimension for obs (with missing values)
6. Averages CMAQ from hourly to daily with time zone awareness

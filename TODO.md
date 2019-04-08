# OVERVIEW

List of functionalities that should be added.

v0.02rc
-------
1. Extend to more obs input formats (currently AMET)
2. Add timezone correction option
3. Test mda8, epamda8
4. Automatically identify obs format/network being supplied
5. Test with CAMx and GEOS-Chem (bpch and new netCDF)
6. Add typical definitions for CMAQ/CAMx and GEOS-Chem
7. Add mechanism for definitions to be maintained by user community


v0.01 - not official release
----------------------------
1. Reads AMET meta-data
2. Reads AMET observations
3. Pairs AMET meta-data and observations
4. Extracts CMAQ at AMET (proxy for PseudoNetCDF funcionality; no IOAPI specific)
5. Adds continuous time dimension for obs (with missing values)
6. Averages CMAQ from hourly to daily with time zone awareness
7. Saves model extract and obs out to netcdf.

__all__ = ['getobsdf']

import numpy as np
import pandas as pd
from datetime import datetime,timedelta

__doc__ = """
All readers must have lat in degrees N, lon in degrees E, dateon_gmt,
and site_id_poc
"""

def getobsdf(args):
    obsfmt = args.obsformat
    reader = eval(obsfmt)
    return reader(args)

def AQSDAILY(args):
    obspath = args.obscsv
    localdatekey = 'Date Local'
    gmtdatekey = 'dateon_gmt'
    read_kwds = dict(
        parse_dates=[localdatekey],
        date_parser=_aqsdateparser,
        dtype={
            'State Code': np.dtype('S2'),
            'County Code': np.dtype('S3'),
            'Site Num': np.dtype('S4'),
            'POC': np.dtype('S4')
        },
    )
    datadf = pd.read_csv(
        obspath,
        **read_kwds
    )
    datadf['site_id_poc'] = (
        datadf['State Code'] +
        datadf['County Code'] +
        datadf['Site Num'] +
        b'-' + datadf['POC']
    )
    datadf['lat'] = datadf['Latitude']
    datadf['lon'] = datadf['Longitude']
    datadf['dateon'] = datadf['Date Local'] # + timedelta(hours=12)
    datadf['dateon_gmt'] = datadf['dateon'] # lst and gmt day are the same in the US
    gbdf = datadf.filter(
                ['Parameter Code', 'Arithmetic Mean', 'Parameter Name']
           ).groupby(['Parameter Code']).max()
    if gbdf.shape[0] != 1:
        raise ValueError('File has more than one Parameter Code; not yet supported')
    name = gbdf.iloc[0]['Parameter Name']
    name = name\
        .replace(' - Local Conditions', '_LC')\
        .replace(' - Standard Conditions', '_SC')\
        .replace('2.5', '25')
    print(gbdf.index[0], name)

    outdf = datadf.rename(columns={'Arithmetic Mean': name})
    outidx = outdf['Sample Duration'] == '24 HOUR'
    eidx = outdf['Event Type'] == 'None'
    
    return outdf[outidx & eidx]

#       'State Code', 'County Code', 'Site Num', 'Parameter Code', 'POC',
#       'Latitude', 'Longitude', 'Datum', 'Parameter Name', 'Sample Duration',
#       'Pollutant Standard', 'Date Local', 'Units of Measure', 'Event Type',
#       'Observation Count', 'Observation Percent', 'Arithmetic Mean',
#       '1st Max Value', '1st Max Hour', 'AQI', 'Method Code', 'Method Name',
#       'Local Site Name', 'Address', 'State Name', 'County Name', 'City Name',
#       'CBSA Name', 'Date of Last Change']

def AMET(args):
    obspath = args.obscsv
    sitepath = args.sitecsv
    localdatekey = 'dateon'
    gmtdatekey = 'dateon_gmt'
    read_kwds = dict(
        dtype={
            'site_id': np.dtype('S16'),
            'POCode': np.dtype('S4')
        },
        parse_dates=[localdatekey],
        date_parser=_ametdateparser
    )

    obsdf = pd.read_csv(
        obspath,
        **read_kwds
    )

    # Read site meta-data and force station id to be a string.
    sitedf = pd.read_csv(
        sitepath, dtype={'stat_id': np.dtype('S16')}
    ).rename(columns={'stat_id': 'site_id'}).set_index('site_id')

    # Join each data point with a unique site
    datadf = obsdf.join(
        sitedf.filter(['site_id', 'GMT_offset', 'lon', 'lat']),
        how='left', on=['site_id'], rsuffix='_site'
    )

    # Add unique identifier including site id and POC
    datadf['site_id_poc'] = datadf.site_id + b'-' + datadf.POCode

    # Add GMT start time
    datadf[gmtdatekey] = (
        datadf[localdatekey] +
        pd.Series([
            pd.Timedelta(g, 'h')
            for g in datadf.GMT_offset
        ], index=datadf.index)
    )
    return datadf


_ametdates = {}

def _ametdateparser(datestr):
    if datestr in _ametdates:
        return _ametdates[datestr]

    _ametdates[datestr] = start = datetime.strptime(
        datestr + '+0000', '%Y-%m-%d %H:%M:%S%z'
    )
    return start


_aqsdates = {}

def _aqsdateparser(datestr):
    if datestr in _aqsdates:
        return _aqsdates[datestr]

    _aqsdates[datestr] = start = datetime.strptime(
        datestr + '+0000', '%Y-%m-%d%z'
    )
    return start



import time
import PseudoNetCDF as pnc
import pandas as pd
import numpy as np
from datetime import datetime
from symtable import symtable
import argparse
from timefuncs import mda8, nstepf
from functools import partial

times = []
times.append(time.time())

parser = argparse.ArgumentParser()
parser.add_argument(
    '--hour-func', default='mean', dest='hourfunc',
    choices=['max', 'mean', 'mda8', 'epamda8'],
    help='Convert hourly model inputs to daily outputs'
)
parser.add_argument('--freq', default='d', choices=['H', 'd'])
parser.add_argument('--variables', help='Subset variables')
parser.add_argument(
    '--mod-format', default='netcdf', dest='modformat',
    help=(
        'PseudoNetCDF format name or keywords' +
        'e.g., "bpch" or "format=\'bpch\',nogroup=True"'
    )
)
parser.add_argument(
    '--obsexpr', action='append', default=[],
    help='String or path defining obs output variables (from obs inputs)')
parser.add_argument(
    '--modexpr', action='append', default=[],
    help='String or path defining mod variables (from mod inputs)'
)
parser.add_argument('sitecsv', help='Path to site meta data')
parser.add_argument('obscsv', help='Path to observation data')
parser.add_argument(
    'modelncs', nargs='+', default=[], help='Path to model files'
)
parser.add_argument('obsoutpath', help='Path to save output')
parser.add_argument('modoutpath', help='Path to save output')

args = parser.parse_args()

sitepath = args.sitecsv
obspath = args.obscsv
inpaths = args.modelncs
modoutpath = args.modoutpath
obsoutpath = args.obsoutpath


_dates = {}


def dateparser(datestr):
    if datestr in _dates:
        return _dates[datestr]

    _dates[datestr] = start = datetime.strptime(
        datestr + '+0000', '%Y-%m-%d %H:%M:%S%z'
    )
    return start


times.append(time.time())
print('Define paths', np.diff(times[-2:]))


modexprstr = '\n'.join([
    open(expri, 'r').read()
    for expri in args.modexpr
])

obsexprstr = '\n'.join([
    open(expri, 'r').read()
    for expri in args.obsexpr
])

# Read site meta-data and force station id to be a string.
sitedf = pd.read_csv(
    sitepath, dtype={'stat_id': np.dtype('S16')}
).rename(columns={'stat_id': 'site_id'}).set_index('site_id')

# Read observation csv and force site_id to be a string
obsdf = pd.read_csv(
    obspath,
    dtype={
        'site_id': np.dtype('S16'),
        'POCode': np.dtype('S4')
    },
    parse_dates=['dateon'],
    date_parser=dateparser
)

# Join each data point with a unique site
datadf = obsdf.join(
    sitedf.filter(['site_id', 'GMT_offset', 'lon', 'lat']),
    how='left', on=['site_id'], rsuffix='_site'
)

# Add unique identifier including site id and POC
datadf['site_id_poc'] = datadf.site_id + b'-' + datadf.POCode

# Add GMT start time
datadf['dateon_gmt'] = (
    datadf.dateon +
    pd.Series([
        pd.Timedelta(g, 'h')
        for g in datadf.GMT_offset
    ], index=datadf.index)
)

times.append(time.time())
print('obs load', np.diff(times[-2:]))

# Open Model Files
# - no read
if '=' in args.modformat:
    modformat = eval('dict(' + args.modformat + ')')
else:
    modformat = dict(format=args.modformat)

infiles = [
    pnc.pncopen(inpath, **modformat)
    for inpath in inpaths
]

# Grab one file to use as a template
tmpfile = infiles[0]

if modexprstr != '':
    symtbl = symtable(modexprstr, '<pncexpr>', 'exec')
    usekeys = [
        s.get_name()
        for s in symtbl.get_symbols()
        if s.is_referenced() and s.get_name() in tmpfile.variables
    ]
    assignkeys = [
        s.get_name() for s in symtbl.get_symbols() if s.is_assigned()
    ]
else:
    usekeys = [k for k in list(tmpfile.variables) if k != 'TFLAG']
    assignkeys = [k for k in usekeys]

times.append(time.time())
print('mod load', np.diff(times[-2:]))

# Get the projection from template file
p = tmpfile.getproj()

# Convert locations to X, Y in projected space
x, y = p(datadf.lon.values, datadf.lat.values)

# Add X/Y/I/J to data frame
datadf['X'] = x
datadf['Y'] = y
datadf['I'] = (x / tmpfile.XCELL).astype('i')
datadf['J'] = (y / tmpfile.YCELL).astype('i')

# Remove values outside of domain
validdf = datadf.query(
    'I > 0 and J > 0 and I < {} and J < {}'.format(
        tmpfile.NCOLS, tmpfile.NROWS
    )
)

times.append(time.time())
print('obs prune', np.diff(times[-2:]))

# Find unique site/I/J values
usij = validdf.groupby(['site_id_poc', 'I', 'J'], as_index=False).mean()


# Extract observations sites
atobsfiles = []
for infile in infiles:
    # Alternative method applies all variables at once
    #  - Higher Memory Requirement
    #  - May be faster
    #
    # atobsfile = infile.sliceDimensions(
    #     ROW=usij.J.values, COL=usij.I.values, newdims=('site_id',)
    # )
    for ki, key in enumerate(usekeys):
        # For each variable, extract and slice
        tk1 = time.time()
        varfile = infile.subsetVariables([key])
        slcfile = varfile.sliceDimensions(
            ROW=usij.J.values, COL=usij.I.values, newdims=('site_id',)
        )
        if ki == 0:
            atobsfile = slcfile
        else:
            # Add to existing
            atobsfile.copyVariable(slcfile.variables[key], key=key)

        tk2 = time.time()
        print(key, tk2 - tk1)

    atobsfile.createDimension('str16', 16)
    var = atobsfile.createVariable('site_key', 'S1', ('site_id', 'str16'))
    var.units = 'site_id'
    var.long_name = 'site_id'.ljust(16)
    var.var_desc = 'site_id'.ljust(80)
    var[:] = usij.site_id_poc.values.astype('S16').view('S1').reshape(-1, 16)
    var = atobsfile.createVariable('longitude', 'f', ('site_id',))
    var.units = 'degrees_east'
    var.long_name = 'longitude'.ljust(16)
    var.var_desc = 'longitude'.ljust(80)
    var[:] = usij.lon.values
    var = atobsfile.createVariable('latitude', 'f', ('site_id',))
    var.units = 'degrees_north'
    var.long_name = 'latitude'.ljust(16)
    var.var_desc = 'latitude'.ljust(80)
    var[:] = usij.lat.values
    atobsfiles.append(atobsfile)

times.append(time.time())
print('mod extract', np.diff(times[-2:]))

# Concatenate files for ouptut
atobsfile = atobsfiles[0].stack(atobsfiles[1:], 'TSTEP')

# Define output variables
outfile = atobsfile.eval(modexprstr)
for key in 'site_key longitude latitude'.split():
    outfile.copyVariable(atobsfile.variables[key], key=key)

if args.freq == 'd':
    if args.hourfunc == 'mda8':
        # Assumes appropriate alignment
        hour2day = partial(mda8, h=24)
    elif args.hourfunc == 'epamda8':
        hour2day = partial(mda8, h=17)
    else:
        mtimes = outfile.getTimes()
        dates = [datetime(t.year, t.month, t.day) for t in mtimes]
        ndates = len(set([datetime(t.year, t.month, t.day) for t in mtimes]))
        ntpd = len(mtimes) / ndates
        if (ntpd % 1) == 0:
            hour2day = partial(nstepf, n=ntpd, func=args.hourfunc)
        else:
            raise ValueError('Input time step is not hourly')

    if hasattr(outfile, 'TSTEP'):
        outfile.TSTEP = 240000

    dayfile = outfile.applyAlongDimensions(TSTEP=hour2day)
    outfile = dayfile
elif args.freq == 'H':
    pass
else:
    raise ValueError('Expected d or H for frequency. Got {}'.format(args.freq))

# Save to disk
outfile.save(modoutpath, format='NETCDF4_CLASSIC')

# Create continuous data
dates = validdf.dateon
start, end = outfile.getTimes()[[0, -1]]
gooddate = (dates >= start) & (dates <= end)
wndwdf = validdf[gooddate]
dates = wndwdf.dateon_gmt
wndwdf.set_index(['site_id_poc', 'dateon_gmt'], inplace=True)
outdf = wndwdf.reindex(pd.MultiIndex.from_product(
    [
        datadf.site_id_poc.unique(),
        pd.date_range(dates.min(), dates.max(), freq=args.freq)
    ],
    names=['site_id_poc', 'dateon_gmt']
)).eval(obsexprstr)

obsfile = outfile.copy()
obssites = obsfile.variables['site_key'].view('S16')[:, 0]
for key in assignkeys:
    ovar = obsfile.variables[key]
    for si, sk in enumerate(obssites):
        sdf = outdf.xs(sk)
        ovar[:, 0, si] = sdf[key]

obsfile.save(obsoutpath)

times.append(time.time())
print('obs output', np.diff(times[-2:]))
print('All', np.sum(np.diff(times)))

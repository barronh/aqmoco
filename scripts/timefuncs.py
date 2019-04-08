def daymean(x):
    """
    Simple daily mean operator. Assumes time axis is already
    aligned to appropriate timezone

    Arguments
    ---------
    x : array-like
        hourly concentrations x(h)

    Returns
    -------
    out : array-like
    """
    return nstepf(x, 24, func='mean')


def nstepf(x, n, func='mean'):
    """
    Arguments
    ---------
    x : array-like
        x must have dimensions that are a multiple of n
    n : int
        n steps to average together

    Returns
    -------
    out : array-like
    """
    shape = [-1, n]
    return getattr(x.reshape(*shape), func)(1)


def mda8(x, h=24):
    """
    calculates Maximum Daily 8-hour average

    Arguments
    ---------
    x : array-like
        hourly concentrations x(h)

    h : int
        choices (24 or 17)
        - 24 all hours of each day are valid
        - 17 intervals starting between 7am and 23 are valid

    Returns
    -------
    out : array-like
        Daily values for mda8 dimension out((h - 24) / 24)
    """
    from functools import partial
    import numpy as np

    n = 8
    fa8 = partial(np.convolve, [1/n] * n, mode='valid')
    a8 = fa8(x)
    
    # complete overlap starts at n - 1
    # if mode == 'valid':
    nedge = 0
    # elif mode = 'full':
    #     nedge = n - 1

    start = nedge
    if h == 17:
        # assuming 0UTC start, the 7am hour is n + 7
        start = n + 7

    nvalid = a8.size - start - nedge
    wholedayhours = int(nvalid // 24 * 24)
    end = start + wholedayhours

    # Use only days with complete data
    usevals = a8[start:end].reshape(-1, 24)

    if h == 17:
        # only 7-23 are valid starting at 7am, that is the first 17
        usevals = usevals[:, :h]
    
    return usevals.max(1)

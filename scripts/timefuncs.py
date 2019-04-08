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

    fa8 = partial(np.convolve, [1/8] * 8, mode='full')
    a8 = fa8(x)
    if h == 24:
        # Trim off invalid steps and incomplete days
        out = a8[4:-20].reshape(-1, 24).max(1)
    elif h == 17:
        # Use days starting at 7am and ending only times starting a 7am
        out = a8[7:-17].reshape(-1, 24)[:, :17].max(1)

    return out

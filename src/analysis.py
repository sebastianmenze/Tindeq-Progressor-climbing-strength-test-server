
import numpy as np


def sigma_clipped_stats(data):
    mask = np.ones(data.shape).astype('bool')
    for i in range(5):
        mean = np.mean(data[mask])
        mask = np.fabs(data-mean) < 4 * np.std(data[mask])
    return data[mask].mean(), np.median(data[mask]), data[mask].std()


def get_edges(f, trigger_level=3):
    rising_edges = np.flatnonzero(np.logical_and(f[:-1] < trigger_level, f[1:] > trigger_level))
    falling_edges = np.flatnonzero(np.logical_and(f[:-1] > trigger_level, f[1:] < trigger_level))
    # check limits
    if f[0] > trigger_level:
        rising_edges = np.insert(rising_edges, 0, 0)
    return rising_edges, falling_edges


def measure_mean_loads(t, f, trigger_level=3):
    """
    Split the data into single work intervals, and calculate mean load in that interval
    """
    rising_edges, falling_edges = get_edges(f, trigger_level)
    fmeans = []; durations = []; fmeds = []; tmeans = []; errs = []
    for s, e in zip(rising_edges, falling_edges):
        if e-s < 3.5:
            continue

        elapsed = t[e]-t[s]
        time = t[s:e].mean()
        mean, med, std = sigma_clipped_stats(f[s:e])
        fmeans.append(mean)
        fmeds.append(med)
        durations.append(elapsed)
        tmeans.append(time)
        errs.append(std / np.sqrt(e-s))
    return (np.array(tmeans), np.array(durations), np.array(fmeans),
            np.array(fmeds), np.array(errs))


def analyse_data(t, f, load_time, rest_time, interactive=False):
    tmeans, durations, _, fmeans, e_fmeans = measure_mean_loads(t, f)
    factor = load_time / (load_time + rest_time)
    load_asymptote = np.nanmean(fmeans[-5:-1])
    e_load_asymptote = np.nanstd(fmeans[-5:-1]) / np.sum(np.isfinite(fmeans[-5:-1]))

    critical_load = load_asymptote * factor
    e_critical_load = critical_load * (e_load_asymptote/load_asymptote)

    used_in_each_interval = (fmeans - critical_load) * durations - critical_load * (load_time+rest_time - durations)
    wprime_alt = np.sum(used_in_each_interval)
    remaining = wprime_alt - np.cumsum(used_in_each_interval)

    # force constant
    alpha = np.median((fmeans - load_asymptote)/remaining)

    msg = '<p>peak load = {:.2f} +/- {:.2f} kg</p>'.format( np.max(fmeans), e_fmeans[0])
    msg += '<p>critical load = {:.2f} +/- {:.2f} kg</p>'.format(critical_load, e_critical_load)
    msg += '<p>asymptotic load = {:.2f} +/- {:.2f} kg</p>'.format(load_asymptote, e_load_asymptote)
    msg += "<p>W'' = {:.0f} J</p>".format(9.8 * wprime_alt)
    msg += '<p>Anaerobic function score = {:.1f}</p>'.format(wprime_alt / critical_load)

    predicted_force = load_asymptote + alpha * remaining

    return tmeans, fmeans, e_fmeans, msg, critical_load, load_asymptote, predicted_force

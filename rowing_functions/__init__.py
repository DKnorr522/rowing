import matplotlib.pyplot as plt
from math import floor, ceil
from datetime import date, datetime


'''
num_oars refers to the number of oars of the boat. A single is used by default
Formula taken from:
https://analytics.rowsandall.com/
2018/03/08/aging-and-rowing-performance-part-4-a-look-at-the-usrowing-age-handicapping-system/
'''
def age_handicap(age, distance=1000, num_oars=2):
    k = {2: .025, 4: .0216, 8: .020}
    p80 = {2: 2.7, 4: 2.3, 8: 2.0}
    age = floor(age)
    hc = ((age-27)**2) * k[num_oars]
    if age > 80:
        hc += p80[num_oars] * (age-80)
    hc = hc * distance / 1000
    return hc


'''
Converts string representation of time to number of seconds
'''
def g_sheets_time_to_sec(time):
    minute, second = time.split(':')
    return float(minute)*60 + float(second)


'''
Converts date from Google Sheets to date object
'''
def g_sheets_time_to_date(day):
    return date.fromisoformat(day.replace('/', '-'))


'''
Converts list of lists of pieces to a dictionary
'''
def g_sheets_to_dict(sheet, main_column="distance"):
    scores = {}

    if main_column == "distance":
        primary = 2; secondary = 0
    else:
        primary = 0; secondary = 2

    for entry in sheet:
        name = entry[primary]
        scores[name] = {}

        scores[name]["date_raw"] = entry[secondary]
        day = g_sheets_time_to_date(entry[0])
        scores[name]["date"] = day

        weight = None if entry[3] == '' else float(entry[3])
        scores[name]["weight"] = weight

        time = g_sheets_time_to_sec(entry[4])
        scores[name]["time"] = time

        split = g_sheets_time_to_sec(entry[5])
        scores[name]["split"] = split

        splits = []
        if len(entry) > 6:
            for split in entry[6:]:
                splits.append(g_sheets_time_to_sec(split))
        scores[name]["splits"] = splits

    return scores


'''
Removes the "distance" column
'''
def get_dict(scores, choice):
    scores_dict = g_sheets_to_dict(scores, choice)
    return scores_dict


'''
Gets proper data from dictionary when "distance" is selected
'''
def chose_distance(distance, piece, tests):
    scores = [test for test in tests if test[0] == piece and test[1] == distance]
    scores_dict = get_dict(scores, "distance")

    return scores_dict


'''
Gets proper data from dictionary when "personal" is selected
'''
def chose_person(person, distance, tests):
    scores = [test for test in tests if test[2] == person and test[1] == distance]
    scores_dict = get_dict(scores, "personal")

    return scores_dict


'''
Converts a number of seconds into its number of minutes, seconds, and microseconds
'''
def secBreakdown(time):
    minute = floor(time / 60)
    second = floor(time - minute*60)
    microsec = floor((time - floor(time)) * 1e6)
    return minute, second, microsec


'''
Creates string in form of readable time from number of minutes, seconds, and microseconds
'''
def breakdownTimePrintout(minute, second, microsec):
    second = f"0{second}" if second < 10 else second
    return f"{minute}:{second}.{int(microsec/1e5)}"


'''
Returns the number of seconds from its datetime representation
'''
def datetime2sec(time):
    return time.minute*60 + time.second + time.microsecond/1e6


'''
Returns a strings for the normal representation of a time from a number of seconds
Input is in seconds
'''
def sec2timePrintout(time):
    minute, second, microsec = secBreakdown(time)
    return breakdownTimePrintout(minute, second, microsec)


'''
Returns the weight adjusted time for a split, given a weight
Simply returns the split if the weight is None
'''
def weightAdjustSplit(split, weight):
    return split if weight is None else round(split * (weight/270)**.222, 1)


'''
Returns the range of times for the y-axis for a given set of rowers and their splits
'''
def determine_split_bounds(rowers, scores):
    min_split = scores[rowers[0]]['splits'][0]
    max_split = scores[rowers[0]]['splits'][0]

    for rower in rowers:
        for split in scores[rower]['splits']:
            min_split = min(min_split, split)
            max_split = max(max_split, split)

    interval = 5  # bounds for the splits will be multiples of 5 seconds
    # Get bounds
    min_bound = (int(min_split) // interval) * interval
    max_bound = ceil((max_split + (max_split-min_bound) / 5) / interval) * interval

    return [min_bound, max_bound]


'''
Returns the size of y-axis tic marks given a plot's y-axis bounds and desired distance between tic marks
'''
def determine_range_scale(bounds, major_interval=15, minor_interval=5):
    major_scale_val = (bounds[0] // major_interval) * major_interval
    major_scale_val = major_scale_val if major_scale_val >= bounds[0] \
        else major_scale_val + major_interval

    major_scale = []
    while major_scale_val <= bounds[1]:
        major_scale.append(major_scale_val)
        major_scale_val += major_interval

    minor_scale_val = (bounds[0] // minor_interval) * minor_interval
    minor_scale_val = minor_scale_val if minor_scale_val >= bounds[0] \
        else minor_scale_val + minor_interval

    minor_scale = []
    while minor_scale_val <= bounds[1]:
        minor_scale.append(minor_scale_val)
        minor_scale_val += minor_interval

    return major_scale, minor_scale


'''
Converts an openpyxl workbook to a dictionary, storing names as keys and the rest as another dictionary
'''
def scores_to_dict(sheet, weight_adj=False):
    scores = {}

    for i in range(sheet.max_row-1):
        name = sheet.cell(row=i+2, column=1).value
        scores[name] = {}
        weight = sheet.cell(row=i+2, column=2).value if weight_adj else None
        scores[name]['weight'] = weight
        scores[name]['time'] = weightAdjustSplit(datetime2sec(sheet.cell(row=i+2, column=3).value), weight)
        split = datetime2sec(sheet.cell(row=i+2, column=4).value)
        scores[name]['split'] = weightAdjustSplit(split, weight)
        scores[name]['split0'] = split  # raw time split, no weight adjustment
        scores[name]['splits'] = []
        for j in range(5, sheet.max_column+1):
            cell_val = sheet.cell(row=i+2, column=j).value
            if cell_val is None:  # if there are no splits (left), dump out
                break
            scores[name]['splits'].append(weightAdjustSplit(datetime2sec(cell_val), weight))

    return scores


'''
Creates plot of rowers' splits
'''
def plot_splits(rowers, scores, dist=1000, weight_adjusted=False, show_splits=True):
    fig, ax = plt.subplots()
    if len(rowers) == 0:  # Exit if this gets called without any rowers, just in case
        return
    if type(rowers) == str:  # If only a single rower is entered as just their name
        rowers = [rowers]
    colors = ['b', 'r', 'g', 'c', 'm', 'y']  # Colors for plotting
    for count, rower in enumerate(rowers):  # Get data for each rower
        splits = scores[rower]['splits']
        weight = scores[rower]['weight']
        color = colors[count]  # Colors assigned in order rowers were selected
        n_splits = len(splits)
        if show_splits and n_splits > 0:  # Only relevant if there are splits to show
            split_size = dist / n_splits
            for i in range(n_splits):
                split = splits[i]
                ax.plot(split_size * (i + 1), split, f'{color}o')
        split = scores[rower]['split']
        lbl = f"{rower}\n{sec2timePrintout(split)}"
        if weight_adjusted:
            addendum = "\nNo Weight" if weight is None else f"\n-{round(scores[rower]['split0']-split, 1)} s"
            lbl += addendum
        ax.axhline(y=split, color=color, linestyle='--', label=lbl)

    ylim = determine_split_bounds(rowers, scores)
    y_major_range, y_minor_range = determine_range_scale(ylim)

    ax.set_xlim((0, dist))
    ax.set_ylim((ylim[0], ylim[1]))

    # Label axes and rest of plot
    plt.xlabel('Distance (m)')
    plt.ylabel('Time (sec)')

    ttl_start = "Weight Adjusted " if weight_adjusted else ""
    plt.title(f"{ttl_start}Splits for {', '.join(rowers)}")
    plt.legend(ncol=len(rowers), loc='upper center')

    ax.grid(True, which='major', color='black', linestyle='-', alpha=.25)
    ax.grid(True, which='minor', color='gray', linestyle='--', alpha=.25)
    ax.minorticks_on()

    return fig

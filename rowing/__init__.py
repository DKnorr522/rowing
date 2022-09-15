import matplotlib.pyplot as plt
from math import floor, ceil


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
    minSplit = scores[rowers[0]]['splits'][0]
    maxSplit = scores[rowers[0]]['splits'][0]

    for rower in rowers:
        for split in scores[rower]['splits']:
            minSplit = min(minSplit, split)
            maxSplit = max(maxSplit, split)

    interval = 5  # bounds for the splits will be multiples of 5 seconds
    # Get bounds
    minBound = (int(minSplit) // interval) * interval
    maxBound = ceil((maxSplit + (maxSplit-minBound) / 5) / interval) * interval

    return [minBound, maxBound]


'''
Returns the size of y-axis tic marks given a plot's y-axis bounds and desired distance between tic marks
'''
def determine_range_scale(bounds, majorInterval=15, minorInterval=5):
    majorScaleVal = (bounds[0] // majorInterval) * majorInterval
    majorScaleVal = majorScaleVal if majorScaleVal >= bounds[0] \
        else majorScaleVal + majorInterval

    majorScale = []
    while majorScaleVal <= bounds[1]:
        majorScale.append(majorScaleVal)
        majorScaleVal += majorInterval

    minorScaleVal = (bounds[0] // minorInterval) * minorInterval
    minorScaleVal = minorScaleVal if minorScaleVal >= bounds[0] \
        else minorScaleVal + minorInterval

    minorScale = []
    while minorScaleVal <= bounds[1]:
        minorScale.append(minorScaleVal)
        minorScaleVal += minorInterval

    return majorScale, minorScale


'''
Converts an openpyxl workbook to a dictionary, storing names as keys and the rest as another dictionary
'''
def scores_to_dict(sheet, weightAdj=False):
    scores = {}

    for i in range(sheet.max_row-1):
        name = sheet.cell(row=i+2, column=1).value
        scores[name] = {}
        weight = sheet.cell(row=i+2, column=2).value if weightAdj else None
        scores[name]['weight'] = weight
        scores[name]['time'] = weightAdjustSplit(datetime2sec(sheet.cell(row=i+2, column=3).value), weight)
        split = datetime2sec(sheet.cell(row=i+2, column=4).value)
        scores[name]['split'] = weightAdjustSplit(split, weight)
        scores[name]['split0'] = split  # raw time split, no weight adjustment
        scores[name]['splits'] = []
        for j in range(5, sheet.max_column+1):
            cellVal = sheet.cell(row=i+2, column=j).value
            if cellVal is None:  # if there are no splits (left), dump out
                break
            scores[name]['splits'].append(weightAdjustSplit(datetime2sec(cellVal), weight))

    return scores


'''
Creates plot of rowers' splits
'''
def plot_splits(rowers, scores, dist=1000, weightAdjusted=False, showSplits=True):
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
        nSplits = len(splits)
        if showSplits and nSplits > 0:  # Only relevant if there are splits to show
            splitSize = dist / nSplits
            for i in range(nSplits):
                split = splits[i]
                ax.plot(splitSize * (i + 1), split, f'{color}o')
        split = scores[rower]['split']
        lbl = f"{rower}\n{sec2timePrintout(split)}"
        if weightAdjusted:
            addendum = "\nNo Weight" if weight is None else f"\n-{round(scores[rower]['split0']-split, 1)} s"
            lbl += addendum
        ax.axhline(y=split, color=color, linestyle='--', label=lbl)

    ylim = determine_split_bounds(rowers, scores)
    yMajorRange, yMinorRange = determine_range_scale(ylim)

    ax.set_xlim((0, dist))
    ax.set_ylim((ylim[0], ylim[1]))

    # Label axes and rest of plot
    plt.xlabel('Distance (m)')
    plt.ylabel('Time (sec)')

    ttlStart = "Weight Adjusted " if weightAdjusted else ""
    plt.title(f"{ttlStart}Splits for {', '.join(rowers)}")
    plt.legend(ncol=len(rowers), loc='upper center')

    ax.grid(True, which='major', color='black', linestyle='-', alpha=.25)
    ax.grid(True, which='minor', color='gray', linestyle='--', alpha=.25)
    ax.minorticks_on()

    # st.pyplot(plt)

    saveName = f"{ttlStart}{', '.join(rowers)}.png"
    
    return (fig, saveName)

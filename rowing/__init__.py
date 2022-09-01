def secBreakdown(time):
    minute = floor(time / 60)
    second = floor(time - minute*60)
    microsec = floor((time - floor(time)) * 1e6)
    return minute, second, microsec


def breakdownTimePrintout(minute, second, microsec):
##    return f"{minute}:{second + round(microsec/1e6, 1)}"
    second = f"0{second}" if second < 10 else second
    return f"{minute}:{second}.{int(microsec/1e5)}"


def datetime2sec(time):
    return time.minute*60 + time.second + time.microsecond/1e6


def sec2timePrintout(time):
    minute, second, microsec = secBreakdown(time)
    return breakdownTimePrintout(minute, second, microsec)


def weightAdjustSplit(split, weight):
    return split if weight is None else round(split * (weight/270)**.222, 1)

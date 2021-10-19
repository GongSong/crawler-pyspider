

THRESHOLD_LAST_SYNC_TIME = 15
THRESHOLD_DIFF_NUMBERS = 0.03


def more_than_threshold(threshold, value):
    if value > threshold:
        return True
    else:
        return False

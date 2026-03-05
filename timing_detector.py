import time


def normalize_key(key):
    try:
        return key.char
    except AttributeError:
        return str(key)


def update_timing_state(key, timing_state):
    now = time.perf_counter()
    current_key = normalize_key(key)

    if timing_state["last_time"] is None:
        timing_state["last_time"] = now
        timing_state["last_key"] = current_key
        return None

    delta = now - timing_state["last_time"]
    timing_state["last_time"] = now

    if current_key != timing_state["last_key"]:
        if timing_state["min_delta"] is None or delta < timing_state["min_delta"]:
            timing_state["min_delta"] = delta

    timing_state["last_key"] = current_key
    return delta

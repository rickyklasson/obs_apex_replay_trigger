from recording_processor import _timestamps_to_highlights

def test_empty():
    assert _timestamps_to_highlights([]) == []

def test_single():
    assert _timestamps_to_highlights([50]) == [(30, 55)]

def test_two_far_apart():
    assert _timestamps_to_highlights([10, 100]) == [(0, 15), (80, 105)]

def test_two_close():
    # Default threshold in code is 20s, so these should merge
    assert _timestamps_to_highlights([10, 25]) == [(0, 30)]

def test_multiple_clusters():
    # 10, 25 are close; 60 is far; 65, 70 are close
    assert _timestamps_to_highlights([10, 25, 60, 65, 70]) == [(0, 30), (40, 75)]

def test_period_start_not_negative():
    # First timestamp is less than 20, so start should be 0
    assert _timestamps_to_highlights([5, 10]) == [(0, 15)]
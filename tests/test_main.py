from hl_research.utils import *

def test_aggregate_price():
    res = get_aggregate_price([
        {'px': '1000', 'sz': 1}, 
        {'px': '2000', 'sz': 2}, 
        {'px': '4000', 'sz': 10}], 
        [100, 1000, 1100, 2000, 10000])
    assert res == {100: 1000.0, 1000: 1000.0, 1100: 1090.909090909091, 2000: 1500.0, 10000.0: 2900.0}

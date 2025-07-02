import datetime
import itertools
import json
from jsondiff import diff
import unittest

import sys
sys.path.append("../src/modules")
import powerwall_tariff as tariff

prev_rates = [{'start': datetime.datetime(2023, 12, 26, 0, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 0, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': -0.01176, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 0, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 1, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.008085, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 1, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 1, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.01155, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 1, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 2, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 2, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 2, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.00462, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 2, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 3, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': -0.00231, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 3, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 3, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.00231, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 3, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 4, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': -0.00462, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 4, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 4, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 4, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 5, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 5, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 5, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': -0.005775, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 5, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 6, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.00903, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 6, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 6, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': -0.0462, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 6, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 7, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0273, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 7, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 7, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.03465, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 7, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 8, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.08883, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 8, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 8, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.01386, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 8, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 9, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.114555, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 9, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 9, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.137025, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 9, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 10, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.16632, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 10, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 10, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.18018, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 10, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 11, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.174405, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 11, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 11, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.17346, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 11, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 12, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.171885, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 12, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 12, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.17094, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 12, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 13, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.17325, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 13, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 13, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.18249, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 13, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 14, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.17325, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 14, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 14, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.179025, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 14, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 15, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.1848, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 15, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 15, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.189, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 15, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 16, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.211575, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 16, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 16, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.336945, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 16, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 17, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.369915, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 17, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 17, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.35931, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 17, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 18, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.35469, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 18, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 18, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.351015, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 18, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 19, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.32928, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 19, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 19, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.20559, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 19, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 20, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.19404, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 20, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 20, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.19635, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 20, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 21, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.17976, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 21, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 21, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.236565, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 21, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 22, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.176925, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 22, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 22, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.1617, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 22, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 23, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.10395, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 23, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 26, 23, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.19656, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 26, 23, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 0, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.15456, 'is_capped': False}]
today_rates = [{'start': datetime.datetime(2023, 12, 27, 0, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 0, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12012, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 0, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 1, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.15015, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 1, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 1, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12243, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 1, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 2, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.09702, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 2, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 2, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.09471, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 2, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 3, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.065625, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 3, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 3, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0924, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 3, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 4, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0651, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 4, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 4, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.09471, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 4, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 5, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.07392, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 5, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 5, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.09471, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 5, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 6, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.085365, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 6, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 6, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.09471, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 6, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 7, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12243, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 7, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 7, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.127785, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 7, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 8, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12936, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 8, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 8, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.10395, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 8, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 9, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.158655, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 9, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 9, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.11088, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 9, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 10, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14427, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 10, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 10, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12201, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 10, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 11, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.151515, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 11, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 11, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12705, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 11, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 12, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14553, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 12, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 12, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14784, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 12, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 13, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14784, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 13, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 13, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14322, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 13, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 14, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.13839, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 14, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 14, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14532, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 14, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 15, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.132405, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 15, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 15, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.1344, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 15, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 16, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.148785, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 16, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 16, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.28497, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 16, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 17, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.304605, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 17, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 17, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.29925, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 17, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 18, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.295995, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 18, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 18, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.295995, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 18, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 19, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.28749, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 19, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 19, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.14595, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 19, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 20, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.12474, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 20, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 20, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.097965, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 20, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 21, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.053445, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 21, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 21, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.05964, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 21, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 22, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.03465, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 22, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 22, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.0462, 'is_capped': False}, {'start': datetime.datetime(2023, 12, 27, 22, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 23, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.01848, 'is_capped': False}]
next_rates = []
export_today_rates = [{'start': datetime.datetime(2023, 12, 27, 0, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 28, 0, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.15, 'is_capped': False}]


def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)


class TestTariff(unittest.TestCase):
    def test_extend_from(self):
        rates = [{'start': datetime.datetime(2023, 12, 27, 1, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 1, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5}]
        tariff.extend_from(rates, datetime.datetime(2023, 12, 27, 0, 0, tzinfo=datetime.timezone.utc))
        expected = [
            {'start': datetime.datetime(2023, 12, 27, 0, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 0, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5},
            {'start': datetime.datetime(2023, 12, 27, 0, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 1, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5},
            {'start': datetime.datetime(2023, 12, 27, 1, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 1, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5}
        ]
        self.assertEqual(expected, rates)

    def test_extend_to(self):
        rates = [{'start': datetime.datetime(2023, 12, 27, 22, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 23, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5}]
        tariff.extend_to(rates, datetime.datetime(2023, 12, 28, 0, 0, tzinfo=datetime.timezone.utc))
        expected = [
            {'start': datetime.datetime(2023, 12, 27, 22, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 23, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5},
            {'start': datetime.datetime(2023, 12, 27, 23, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 27, 23, 30, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5},
            {'start': datetime.datetime(2023, 12, 27, 23, 30, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2023, 12, 28, 0, 0, tzinfo=datetime.timezone.utc), 'value_inc_vat': 0.5}
        ]
        self.assertEqual(expected, rates)

    def test_multiday_schedule_type_start_of_week(self):
        schedule1 = AllDaySchedule(datetime.date(2024, 3, 4))
        schedule2 = AllDaySchedule(datetime.date(2024, 3, 5))
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(0, [schedule1], None)
        week_schedules.update(1, [schedule2], None)
        data = tariff.schedules_to_tariff(week_schedules, "multiday", None)
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["fromDayOfWeek"])
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["toDayOfWeek"])
        self.assertEqual(1, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["fromDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["toDayOfWeek"])

    def test_multiday_schedule_type_midweek(self):
        schedule1 = AllDaySchedule(datetime.date(2024, 3, 7))
        schedule2 = AllDaySchedule(datetime.date(2024, 3, 8))
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(3, [schedule1], None)
        week_schedules.update(4, [schedule2], None)
        data = tariff.schedules_to_tariff(week_schedules, "multiday", None)
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["fromDayOfWeek"])
        self.assertEqual(3, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["toDayOfWeek"])
        self.assertEqual(4, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["fromDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["toDayOfWeek"])

    def test_multiday_schedule_type_end_of_week(self):
        schedule1 = AllDaySchedule(datetime.date(2024, 3, 9))
        schedule2 = AllDaySchedule(datetime.date(2024, 3, 10))
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(5, [schedule1], None)
        week_schedules.update(6, [schedule2], None)
        data = tariff.schedules_to_tariff(week_schedules, "multiday", None)
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["fromDayOfWeek"])
        self.assertEqual(5, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["toDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["fromDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["toDayOfWeek"])

    def test_multiday_schedule_type_rollover(self):
        schedule1 = AllDaySchedule(datetime.date(2024, 3, 10))
        schedule2 = AllDaySchedule(datetime.date(2024, 3, 11))
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(6, [schedule1], None)
        week_schedules.update(0, [schedule2], None)
        data = tariff.schedules_to_tariff(week_schedules, "multiday", None)
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["fromDayOfWeek"])
        self.assertEqual(5, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["toDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["fromDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["toDayOfWeek"])

    def test_multiday_schedule_type_roll_disjoint(self):
        schedule1 = AllDaySchedule(datetime.date(2024, 3, 7))
        schedule2 = AllDaySchedule(datetime.date(2024, 3, 9))
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(3, [schedule1], None)
        week_schedules.update(5, [schedule2], None)
        data = tariff.schedules_to_tariff(week_schedules, "multiday", None)
        self.assertEqual(0, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["fromDayOfWeek"])
        self.assertEqual(4, data["Summer"]["tou_periods"]["OFF_PEAK"][0]["toDayOfWeek"])
        self.assertEqual(5, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["fromDayOfWeek"])
        self.assertEqual(6, data["Summer"]["tou_periods"]["OFF_PEAK"][1]["toDayOfWeek"])

    def test_calculate_tariff_3_breaks(self):
        tariff_breaks = [0.1, 0.2, 0.3]
        tariff_pricing = ["average", "average", "average", "average"]
        day = datetime.date(2023, 12, 27)
        import_rates = tariff.Rates()
        import_rates.previous_day = prev_rates
        import_rates.current_day = today_rates
        import_rates.next_day = next_rates

        day_rates = import_rates.cover_day(day)
        import_schedules = tariff.get_schedules(tariff_breaks, tariff_pricing, None, day, day_rates)
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(day.weekday(), import_schedules, None)
        data = tariff.to_tariff_data("Test", "Test plan", 0, "week", "Test plan", 0, "week", week_schedules, day)
        expected = load_json("tests/expected_3_breaks.json")
        self.assertFalse(diff(expected, data), msg=f"\nActual:\n{json.dumps(data)}")

    def test_calculate_tariff_5_breaks(self):
        tariff_breaks = [0.1, 0.15, 0.2, 0.25, 0.3]
        tariff_pricing = ["average", "average", "average", "average", "average", "average"]
        day = datetime.date(2023, 12, 27)
        import_rates = tariff.Rates()
        import_rates.previous_day = prev_rates
        import_rates.current_day = today_rates
        import_rates.next_day = next_rates

        day_rates = import_rates.cover_day(day)
        import_schedules = tariff.get_schedules(tariff_breaks, tariff_pricing, None, day, day_rates)
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(day.weekday(), import_schedules, None)
        data = tariff.to_tariff_data("Test", "Test plan", 0, "week", "Test plan", 0, "week", week_schedules, day)
        expected = load_json("tests/expected_5_breaks.json")
        self.assertFalse(diff(expected, data), msg=f"\nActual:\n{json.dumps(data)}")

    def test_calculate_tariff_individual_breaks(self):
        tariff_breaks = "individual"
        tariff_pricing = "average"
        day = datetime.date(2023, 12, 27)
        import_rates = tariff.Rates()
        import_rates.previous_day = prev_rates
        import_rates.current_day = today_rates
        import_rates.next_day = next_rates
        export_rates = tariff.Rates()
        export_rates.current_day = export_today_rates

        import_day_rates = import_rates.cover_day(day)
        export_day_rates = export_rates.cover_day(day)
        import_schedules = tariff.get_schedules(tariff_breaks, tariff_pricing, None, day, import_day_rates)
        export_schedules = tariff.get_schedules(tariff_breaks, tariff_pricing, None, day, export_day_rates)
        week_schedules = tariff.WeekSchedules()
        week_schedules.update(day.weekday(), import_schedules, export_schedules)
        data = tariff.to_tariff_data("Test", "Test plan", 0, "week", "Test plan", 0, "week", week_schedules, day)
        expected = load_json("tests/expected_individual_breaks.json")
        self.assertFalse(diff(expected, data), msg=f"\nActual:\n{json.dumps(data)}")


class AllDaySchedule:
    def __init__(self, day_date):
        self.charge_name = "OFF_PEAK"
        self.periods = [(datetime.datetime.combine(day_date, datetime.time.min), datetime.datetime.combine(day_date + datetime.timedelta(days=1), datetime.time.min))]

    def get_periods(self):
        return self.periods

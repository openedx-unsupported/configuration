import unittest
import datetime
from check_celery_progress import build_new_state, datetime_from_str

class TestCheckCeleryQueues(unittest.TestCase):
    queue_first_items_0 = {
        'edx.lms.core.grades_policy_change':
            b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "8a661b24-cf3a-49f6-ba72-824d20d1cc02", "reply_to": "9d88dd87-c55f-3d95-a725-176db14a16dd", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.grades_policy_change", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "0efb9ecc-2914-4a3c-98fb-358a67d678d8"}, "content-encoding": "utf-8"}',
        'edx.lms.core.default':
            b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "27d76be4-408b-4f5b-a132-5ad043465e90", "reply_to": "2e6506c2-46dd-3dd7-9be0-a03e0e5c2f7f", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.default", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "2627a9a2-1941-4890-8fe3-c477c62b707d"}, "content-encoding": "utf-8"}'
    }
    queue_first_items_1 = {
        'edx.lms.core.grades_policy_change':
            b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "8a661b24-cf3a-49f6-ba72-824d20d1cc02", "reply_to": "9d88dd87-c55f-3d95-a725-176db14a16dd", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.grades_policy_change", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "0efb9ecc-2914-4a3c-98fb-358a67d678d8"}, "content-encoding": "utf-8"}',
        'edx.lms.core.default':
            b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "27d76be4-408b-4f5b-a132-c0ffee465e90", "reply_to": "2e6506c2-46dd-3dd7-9be0-a03e0e5c2f7f", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.default", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "2627a9a2-1941-4890-8fe3-c477c62b707d"}, "content-encoding": "utf-8"}'
    }
    queue_first_items_2 = {
        'edx.lms.core.grades_policy_change': b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "be36d7d2-a63c-422c-b348-4c58c65cfd31", "reply_to": "d08d8e41-177d-35eb-a496-37018b1779cd", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.grades_policy_change", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "0e40a1f2-4b9a-4606-8d9d-79ee864cfbb0"}, "content-encoding": "utf-8"}',
        'edx.lms.core.default':
            b'{"body": "", "headers": {"compression": "application/x-gzip"}, "content-type": "application/json", "properties": {"body_encoding": "base64", "correlation_id": "4004a64c-dd21-4691-a114-ffec735e2851", "reply_to": "f04c9aa4-57b8-31c2-addf-31cb7061072b", "delivery_info": {"priority": 0, "routing_key": "edx.lms.core.default", "exchange": "edx.lms.core"}, "delivery_mode": 2, "delivery_tag": "373ebf18-b4af-474a-a8e8-e9c56b6e9491"}, "content-encoding": "utf-8"}'
    }
    time_0 = datetime_from_str("2018-10-04 11:00:51.111367")
    time_1_min = datetime_from_str("2018-10-04 11:01:51.111367")
    time_10_min = datetime_from_str("2018-10-04 11:10:51.111367")

    def test_equal_output_if_queues_stuck(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_1 = build_new_state(state_0, self.queue_first_items_0, self.time_1_min)
        self.assertEqual(state_0, state_1)

    def test_output_1_queue_changed(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_1 = build_new_state(state_0, self.queue_first_items_1, self.time_1_min)
        self.assertEqual(state_0['edx.lms.core.grades_policy_change'], state_1['edx.lms.core.grades_policy_change'])
        self.assertEqual(state_1['edx.lms.core.default']['first_occurance_time'], self.time_1_min)
        self.assertEqual(state_1['edx.lms.core.default']['correlation_id'], "27d76be4-408b-4f5b-a132-c0ffee465e90")

if __name__ == '__main__':
    unittest.main()

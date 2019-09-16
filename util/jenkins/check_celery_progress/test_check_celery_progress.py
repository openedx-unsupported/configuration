from __future__ import absolute_import
import unittest
import datetime
from datetime import timedelta
from check_celery_progress import build_new_state, datetime_from_str, should_create_alert, pack_state, unpack_state

class TestCheckCeleryQueues(unittest.TestCase):
    
    queue_first_items_0 = {
        "edx.lms.core.grades_policy_change": {
            "body": "",
            "headers": {
                "compression": "application/x-gzip"
            },
            "content-type": "application/json",
            "properties": {
                "body_encoding": "base64",
                "correlation_id": "8a661b24-cf3a-49f6-ba72-824d20d1cc02",
                "reply_to": "9d88dd87-c55f-3d95-a725-176db14a16dd",
                "delivery_info": {
                    "priority": 0,
                    "routing_key": "edx.lms.core.grades_policy_change",
                    "exchange": "edx.lms.core"
                },
                "delivery_mode": 2,
                "delivery_tag": "0efb9ecc-2914-4a3c-98fb-358a67d678d8"
            },
            "content-encoding": "utf-8"
        },
        "edx.lms.core.default": {
            "body": "",
            "headers": {
                "compression": "application/x-gzip"
            },
            "content-type": "application/json",
            "properties": {
                "body_encoding": "base64",
                "correlation_id": "27d76be4-408b-4f5b-a132-5ad043465e90",
                "reply_to": "2e6506c2-46dd-3dd7-9be0-a03e0e5c2f7f",
                "delivery_info": {
                    "priority": 0,
                    "routing_key": "edx.lms.core.default",
                    "exchange": "edx.lms.core"
                },
                "delivery_mode": 2,
                "delivery_tag": "2627a9a2-1941-4890-8fe3-c477c62b707d"
            },
            "content-encoding": "utf-8"
        }
    }
    
    
    queue_first_items_1 = {
        "edx.lms.core.grades_policy_change": {
            "body": "",
            "headers": {
                "compression": "application/x-gzip"
            },
            "content-type": "application/json",
            "properties": {
                "body_encoding": "base64",
                "correlation_id": "8a661b24-cf3a-49f6-ba72-824d20d1cc02",
                "reply_to": "9d88dd87-c55f-3d95-a725-176db14a16dd",
                "delivery_info": {
                    "priority": 0,
                    "routing_key": "edx.lms.core.grades_policy_change",
                    "exchange": "edx.lms.core"
                },
                "delivery_mode": 2,
                "delivery_tag": "0efb9ecc-2914-4a3c-98fb-358a67d678d8"
            },
            "content-encoding": "utf-8"
        },
        "edx.lms.core.default": {
            "body": "",
            "headers": {
                "compression": "application/x-gzip"
            },
            "content-type": "application/json",
            "properties": {
                "body_encoding": "base64",
                "correlation_id": "27d76be4-408b-4f5b-a132-c0ffee465e90",
                "reply_to": "2e6506c2-46dd-3dd7-9be0-a03e0e5c2f7f",
                "delivery_info": {
                    "priority": 0,
                    "routing_key": "edx.lms.core.default",
                    "exchange": "edx.lms.core"
                },
                "delivery_mode": 2,
                "delivery_tag": "2627a9a2-1941-4890-8fe3-c477c62b707d"
            },
            "content-encoding": "utf-8"
        }
    }

    time_0 = datetime_from_str("2018-10-04 11:00:51.111367")
    time_1_min = datetime_from_str("2018-10-04 11:01:51.111367")

    threshold = 5 * 60

    def test_equal_output_if_queues_stuck(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_1 = build_new_state(state_0, self.queue_first_items_0, self.time_1_min)
        self.assertEqual(state_0, state_1)

    def test_build_new_state_missing_alert_created(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_0['edx.lms.core.default'].pop('alert_created')
        state_1 = build_new_state(state_0, self.queue_first_items_0, self.time_1_min)
        self.assertFalse(state_1['edx.lms.core.default']['alert_created'])

    def test_build_new_state_alert_created(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_1 = build_new_state(state_0, self.queue_first_items_0, self.time_1_min)
        self.assertFalse(state_0['edx.lms.core.grades_policy_change']['alert_created'])
        self.assertFalse(state_0['edx.lms.core.default']['alert_created'])
        self.assertFalse(state_1['edx.lms.core.grades_policy_change']['alert_created'])
        self.assertFalse(state_1['edx.lms.core.default']['alert_created'])

    def test_build_new_state_alert_created_preserved(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_0['edx.lms.core.default']['alert_created'] = True
        state_1 = build_new_state(state_0, self.queue_first_items_0, self.time_1_min)
        self.assertTrue(state_1['edx.lms.core.default']['alert_created'])

    def test_output_1_queue_changed(self):
        state_0 = build_new_state({}, self.queue_first_items_0, self.time_0)
        state_1 = build_new_state(state_0, self.queue_first_items_1, self.time_1_min)
        self.assertEqual(state_0['edx.lms.core.grades_policy_change'], state_1['edx.lms.core.grades_policy_change'])
        self.assertEqual(state_1['edx.lms.core.default']['first_occurance_time'], self.time_1_min)
        self.assertEqual(state_1['edx.lms.core.default']['correlation_id'], "27d76be4-408b-4f5b-a132-c0ffee465e90")
        self.assertFalse(state_1['edx.lms.core.default']['alert_created'])

    def test_should_create_alert_0_delta(self):
        first_occurance_time = self.time_0
        result = should_create_alert(first_occurance_time, self.time_0, self.threshold)
        self.assertEqual(False, result)

    def test_should_create_alert_under_threshold(self):
        first_occurance_time = self.time_0 - timedelta(seconds=self.threshold-60)
        result = should_create_alert(first_occurance_time, self.time_0, self.threshold)
        self.assertEqual(False, result)

    def test_should_create_alert_over_threshold(self):
        first_occurance_time = self.time_0 - timedelta(seconds=self.threshold+60)
        result = should_create_alert(first_occurance_time, self.time_0, self.threshold)
        self.assertEqual(True, result)

    def test_should_create_alert_negative_delta(self):
        first_occurance_time = self.time_0 + timedelta(seconds=self.threshold+60)
        result = should_create_alert(first_occurance_time, self.time_0, self.threshold)
        self.assertEqual(False, result)

    def test_pack_state(self):
        # Round trip state to make sure all fields are preserved
        state = build_new_state({}, self.queue_first_items_0, self.time_0)
        packed_state = pack_state(state)
        encoded_packed_state = {k.encode("utf-8"): v.encode("utf-8") for k, v in packed_state.items()}
        unpacked_state = unpack_state(encoded_packed_state)
        self.assertEqual(state, unpacked_state)


if __name__ == '__main__':
    unittest.main()

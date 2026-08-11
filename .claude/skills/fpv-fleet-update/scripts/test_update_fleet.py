#!/usr/bin/env python3
import unittest

import update_fleet as fleet


class ModeExtractionTests(unittest.TestCase):
    def test_range_visual_is_compact_but_keeps_25_microsecond_boundaries(self):
        self.assertEqual(
            fleet.mode_range_visual(900, 1300),
            '900 |████████················| 2100',
        )
        self.assertEqual(
            fleet.mode_range_visual(925, 1425),
            '900 |▐█████████▌·············| 2100',
        )

    def test_extracts_mode_name_channel_range_and_condition_fields(self):
        modes = fleet.extract_modes("\n".join([
            "aux 0 0 0 900 1300 0 0",
            "aux 3 26 3 1300 1700 1 39",
        ]))

        self.assertEqual(modes, [
            {
                'slot': 0, 'mode_id': 0, 'mode': 'ARM', 'aux_channel': 'AUX1',
                'range_start': 900, 'range_end': 1300,
                'range_visual': '900 |████████················| 2100', 'logic': 'OR',
                'linked_to_id': '', 'linked_to': '',
            },
            {
                'slot': 3, 'mode_id': 26, 'mode': 'BLACKBOX', 'aux_channel': 'AUX4',
                'range_start': 1300, 'range_end': 1700,
                'range_visual': '900 |········████████········| 2100', 'logic': 'AND',
                'linked_to_id': 39, 'linked_to': 'VTX PIT MODE',
            },
        ])

    def test_keeps_unknown_mode_ids_and_ignores_disabled_ranges(self):
        modes = fleet.extract_modes("\n".join([
            "aux 0 99 1 1700 2100 0 0",
            "aux 1 13 2 1500 1500 0 0",
        ]))

        self.assertEqual(len(modes), 1)
        self.assertEqual(modes[0]['mode'], 'UNKNOWN (99)')


class ModeViewTests(unittest.TestCase):
    def test_requires_active_status_discipline_and_class(self):
        base = {
            'quad': 'Test', 'discipline': 'race', 'class': 'whoop',
            'status': '', 'bf_version': '4.5.2', 'file': 'dump.txt',
            '_modes': fleet.extract_modes('aux 0 0 0 900 1300 0 0'),
        }

        self.assertEqual(len(fleet.build_mode_rows([base])), 1)
        self.assertEqual(fleet.build_mode_rows([{**base, 'status': 'retired'}]), [])
        self.assertEqual(fleet.build_mode_rows([{**base, 'discipline': ''}]), [])
        self.assertEqual(fleet.build_mode_rows([{**base, 'class': ''}]), [])


if __name__ == '__main__':
    unittest.main()

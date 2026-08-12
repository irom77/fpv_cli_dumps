#!/usr/bin/env python3
import unittest

import update_fleet as fleet


class ModeExtractionTests(unittest.TestCase):
    def test_range_visual_is_compact_but_keeps_25_microsecond_boundaries(self):
        visual = fleet.mode_range_visual(900, 1300)
        cells = visual.removeprefix('900 |').removesuffix('| 2100')
        self.assertEqual(set(cells) - {'░', '█', '▌', '▐'}, set())
        self.assertEqual(
            visual,
            '900 |████████░░░░░░░░░░░░░░░░| 2100',
        )
        self.assertEqual(
            fleet.mode_range_visual(925, 1425),
            '900 |▐█████████▌░░░░░░░░░░░░░| 2100',
        )

    def test_extracts_mode_name_channel_range_and_condition_fields(self):
        modes = fleet.extract_modes("\n".join([
            "aux 0 0 0 900 1300 0 0",
            "aux 3 26 3 1300 1700 1 39",
        ]))

        self.assertEqual(modes, [
            {
                'slot': 0, 'mode_id': 0, 'mode': 'ARM', 'aux_channel': '🔴 AUX1',
                'range_start': 900, 'range_end': 1300,
                'range_visual': '900 |████████░░░░░░░░░░░░░░░░| 2100', 'logic': 'OR',
                'linked_to_id': '', 'linked_to': '',
            },
            {
                'slot': 3, 'mode_id': 26, 'mode': 'BLACKBOX', 'aux_channel': '⚫ AUX4',
                'range_start': 1300, 'range_end': 1700,
                'range_visual': '900 |░░░░░░░░████████░░░░░░░░| 2100', 'logic': 'AND',
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

    def test_groups_modes_by_aux_then_orders_each_switch_low_to_high(self):
        row = {
            'quad': 'Test', 'discipline': 'race', 'class': '5-inch', 'status': 'active',
            'bf_version': '4.5.2', 'file': 'dump.txt',
            '_modes': fleet.extract_modes('\n'.join([
                'aux 0 0 0 900 1300 0 0',
                'aux 1 1 1 1700 2100 0 0',
                'aux 2 13 2 1700 2100 0 0',
                'aux 3 26 3 1700 2100 0 0',
                'aux 4 28 1 900 1300 0 0',
                'aux 5 35 1 1300 1700 0 0',
            ])),
        }

        modes = fleet.build_mode_rows([row])

        self.assertEqual(
            [(mode['aux_channel'], mode['range_start'], mode['mode']) for mode in modes],
            [
                ('🔴 AUX1', 900, 'ARM'),
                ('🔵 AUX2', 900, 'AIRMODE'),
                ('🔵 AUX2', 1300, 'FLIP OVER AFTER CRASH'),
                ('🔵 AUX2', 1700, 'ANGLE'),
                ('🟢 AUX3', 1700, 'BEEPER ON'),
                ('⚫ AUX4', 1700, 'BLACKBOX'),
            ],
        )

    def test_compact_view_blanks_repeated_group_fields_only(self):
        rows = [
            {'quad': 'A', 'discipline': 'race', 'class': 'whoop', 'mode': 'ARM'},
            {'quad': 'A', 'discipline': 'race', 'class': 'whoop', 'mode': 'ANGLE'},
            {'quad': 'B', 'discipline': 'race', 'class': 'whoop', 'mode': 'ARM'},
            {'quad': 'C', 'discipline': 'freestyle', 'class': '5-inch', 'mode': 'ARM'},
        ]

        compact = fleet.compact_mode_groups(rows)

        self.assertEqual(compact, [
            {'quad': 'A', 'discipline': 'race', 'class': 'whoop', 'mode': 'ARM'},
            {'quad': '', 'discipline': '', 'class': '', 'mode': 'ANGLE'},
            {'quad': 'B', 'discipline': '', 'class': '', 'mode': 'ARM'},
            {'quad': 'C', 'discipline': 'freestyle', 'class': '5-inch', 'mode': 'ARM'},
        ])
        self.assertEqual(rows[1]['quad'], 'A')  # output compaction does not mutate parsed rows


class LatestMarkerTests(unittest.TestCase):
    def test_same_day_pre_and_post_flash_dumps_have_one_latest_row(self):
        rows = [
            {
                '_ident': 'OPENRACER', 'dump_date': '2026-08-12',
                'file': 'BTFL_cli_backup_OPENRACER_20260812_120242_BOARD.txt', 'note': '',
            },
            {
                '_ident': 'OPENRACER', 'dump_date': '2026-08-12',
                'file': 'BTFL_cli_backup_OPENRACER_20260812_122055_BOARD.txt', 'note': '',
            },
        ]

        fleet.mark_latest_rows(rows)

        self.assertEqual(rows[0]['note'], '')
        self.assertEqual(rows[1]['note'], 'latest')


if __name__ == '__main__':
    unittest.main()

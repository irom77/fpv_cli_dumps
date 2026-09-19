"""Regression using the local, gitignored crash log; skips when unavailable."""
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / 'blackbox/BTFL_BLACKBOX_LOG_CINE-FISH_20260918_172219_GEPRCF411_AIO.BBL'


@unittest.skipUnless(LOG.exists(), 'Local Cine-fish Blackbox fixture unavailable')
class CineFishAnalysisTest(unittest.TestCase):
    def test_runaway_events_and_missing_rpm_are_reported(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / '.claude/skills/fpv-bbl-analyze/scripts/analyze_bbl.py'), str(LOG)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.count('RUNAWAY_TAKEOFF (reason=6'), 2)
        self.assertEqual(result.stdout.count('four-motor RPM telemetry absent'), 2)
        self.assertEqual(result.stdout.count('Log End Event:   present'), 2)
        self.assertNotIn('Control Loop:    Clean', result.stdout)
        self.assertNotIn('MOTOR_DESYNC detected', result.stdout)


if __name__ == '__main__':
    unittest.main()

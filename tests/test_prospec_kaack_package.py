import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "upgrades" / "PROSPEC_KAACK_V19_UPGRADE"
FIRMWARE = PACKAGE / "betaflight_4.5.3.KAACK_V19_STM32F7X2_HOBBYWING_XROTORF7CON.hex"
RESTORE = PACKAGE / "BTFL_cli_restore_PROSPEC_20260825_KAACK_V19.txt"


def test_firmware_is_valid_intel_hex_for_exact_prospec_target():
    lines = FIRMWARE.read_text(encoding="ascii").splitlines()
    memory = {}
    base = 0

    assert lines[-1] == ":00000001FF"
    for line in lines:
        record = bytes.fromhex(line[1:])
        assert line.startswith(":")
        assert len(record) == record[0] + 5
        assert sum(record) & 0xFF == 0
        length, address, record_type = record[0], int.from_bytes(record[1:3], "big"), record[3]
        data = record[4 : 4 + length]
        if record_type == 0:
            memory.update((base + address + offset, byte) for offset, byte in enumerate(data))
        elif record_type == 4:
            base = int.from_bytes(data, "big") << 16

    payload = FIRMWARE.read_bytes()
    assert len(payload) > 500_000
    first_address = min(memory)
    decoded = bytearray(b"\xff") * (max(memory) - first_address + 1)
    for address, byte in memory.items():
        decoded[address - first_address] = byte
    assert b"4.5.3.KAACK_V19" in decoded
    assert b"HOBBYWING_XROTORF7CONV" in decoded
    assert b"HOWI" in decoded


def test_restore_selects_mgp_pro_13k_and_preserves_known_hardware_settings():
    restore = RESTORE.read_text(encoding="utf-8")

    required = {
        "feature RX_SERIAL",
        "set serialrx_provider = SBUS",
        "set motor_pwm_protocol = DSHOT600",
        "set dshot_bidir = ON",
        "set motor_poles = 14",
        "set motor_kv = 1300",
        "set rpm_limit = ON",
        "set rpm_limit_p = 25",
        "set rpm_limit_i = 10",
        "set rpm_limit_d = 8",
        "set rpm_limit_value = 13000",
        "set craft_name = prospec",
    }
    assert required <= set(restore.splitlines())
    assert "rpm_limit_value = 18000" not in restore
    assert "FREEDOM 18K" not in restore
    assert restore.rstrip().endswith("save")


def test_manifest_authenticates_every_recovery_artifact():
    entries = {}
    for line in (PACKAGE / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, filename = line.split("  ", 1)
        entries[filename] = digest

    expected_files = {FIRMWARE.name, RESTORE.name, "README.md"}
    assert set(entries) == expected_files
    for filename, expected_digest in entries.items():
        actual_digest = hashlib.sha256((PACKAGE / filename).read_bytes()).hexdigest()
        assert actual_digest == expected_digest

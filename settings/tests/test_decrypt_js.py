"""Runs the Node WebCrypto round-trip self-test for the AAPS decryptor.

Skips when Node is unavailable, so the Python suite stays green in environments without it.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

DECRYPT_DIR = Path(__file__).resolve().parents[1] / "decrypt"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def test_aaps_decrypt_roundtrip_node():
    result = subprocess.run(
        ["node", "--test", "roundtrip.test.mjs"],
        cwd=str(DECRYPT_DIR), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"node tests failed:\n{result.stdout}\n{result.stderr}"
    assert "pass 3" in result.stdout or "# pass 3" in result.stdout


# What Trio's Export Settings writes (SettingsExportStateModel.swift): a byte-order mark, this
# header, one row per setting named by its screen label, percentages as whole numbers and
# glucose in the app's units. The last row is not one Trio writes; it is there so that a known
# label outside Therapy and Algorithm is shown to be ignored.
TRIO_EXPORT = """﻿Setting Category,Subcategory,Setting Name,Value,Unit
Metadata,,Export Date,"Nov 15, 2026 at 10:00:00 AM",
Therapy,Units and Limits,Glucose Units,mmol/L,
Therapy,Units and Limits,Maximum Insulin on Board (IOB),6.5,U
Therapy,Units and Limits,Maximum Basal Rate,4,U/hr
Therapy,Units and Limits,Maximum Carbs on Board (COB),120,g
Therapy,Glucose Targets,Target (00:00),5.5,mmol/L
Algorithm,Autosens,Autosens Max,120,%
Algorithm,Autosens,Autosens Min,70 (mode is using 100),%
Algorithm,SMB,Enable SMB Always,Enabled,
Algorithm,SMB,Enable SMB With COB,Disabled,
Algorithm,SMB,Enable SMB With High Glucose,Enabled,
Algorithm,SMB,High Glucose Target,6.1,mmol/L
Algorithm,SMB,Enable UAM,Enabled,
Algorithm,SMB,Max SMB Basal Minutes,60,minutes
Algorithm,SMB,Max UAM Basal Minutes,45,minutes
Algorithm,Dynamic Settings,Dynamic ISF,Logarithmic,
Algorithm,Additionals,Max Daily Safety Multiplier,300,%
Algorithm,Additionals,Current Basal Safety Multiplier,400,%
Algorithm,Additionals,Use Custom Peak Time,Enabled,
Algorithm,Additionals,Insulin Peak Time,55,minutes
Algorithm,Additionals,SMB Delivery Ratio,50,%
Temp Target Presets,"Exercise, long",Target,8.0,mmol/L
Override Presets,Sport,Max SMB Basal Minutes,0,minutes
"""


def test_trio_export_read_by_the_page_loader_and_the_validator(tmp_path):
    from report.browser import settings_from_raw

    web = DECRYPT_DIR.parents[1] / "web"
    if not (web / "aaps_prefs.mjs").exists():       # web/build.sh puts it there; settings.js imports it
        shutil.copy(DECRYPT_DIR / "aaps_prefs.mjs", web / "aaps_prefs.mjs")
    export = tmp_path / "TrioSettings_20261115_100000.csv"
    export.write_text(TRIO_EXPORT, encoding="utf-8")
    result = subprocess.run(
        ["node", "--input-type=module", "-e",
         "import { readFileSync } from 'node:fs';"
         "import { loadSettingsFromFile } from './settings.js';"
         "const file = new File([readFileSync(process.argv[1])], 'TrioSettings.csv');"
         "console.log(JSON.stringify(await loadSettingsFromFile(file, '')));",
         str(export)],
        cwd=str(web), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stdout)
    assert loaded["format"] == "Trio export"
    assert loaded["unread"] == ["Autosens Min"]     # annotated by the dosing mode, so left out
    assert loaded["collisions"] == []

    parsed = settings_from_raw(loaded["raw"])
    assert parsed["blocked"] == []
    high_bg = parsed["settings"].pop("enable_smb_high_bg_target")
    assert high_bg == pytest.approx(6.1 * 18.0182)
    assert parsed["settings"] == {
        "max_iob": 6.5, "max_basal": 4.0,
        "max_daily_safety_multiplier": 3.0, "current_basal_safety_multiplier": 4.0,
        "max_smb_minutes": 60, "max_uam_minutes": 45,
        "enable_smb_always": True, "enable_smb_with_cob": False,
        "enable_smb_high_bg": True, "enable_smb_uam": True,
        "insulin_peak_min": 55,
    }
    advisory = {k: parsed["all_values"][k] for k in
                ("max_cob", "autosens_max", "smb_delivery_ratio", "dynamic_isf_enabled")}
    assert advisory == {"max_cob": 120, "autosens_max": 1.2, "smb_delivery_ratio": 0.5,
                        "dynamic_isf_enabled": True}
    assert "autosens_min" not in parsed["all_values"]
    assert "target_bg" not in parsed["all_values"]

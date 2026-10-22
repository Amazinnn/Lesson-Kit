"""Key feedback cues: four short, self-made assets plus the module behaviour.

The assets are synthesised from scratch (tests/workbench/sfx_assets.py); these
checks fail if an asset is replaced by a downloaded or hand-edited file.
"""

import array
import subprocess
import sys
import wave
from pathlib import Path

from tests.workbench import sfx_assets


REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_TEST = Path(__file__).with_name("sfx.test.js")
AUDIO_DIR = REPO_ROOT / "workbench" / "server" / "static" / "assets" / "audio"


def _samples(raw):
    values = array.array("h")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()
    return values


def test_sfx_module_behaviour():
    result = subprocess.run(
        ["node", "--test", str(NODE_TEST)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output


def test_only_the_four_cues_are_shipped():
    shipped = sorted(path.name for path in AUDIO_DIR.glob("*") if path.is_file())
    assert shipped == sorted(sfx_assets.FILES.values())


def test_every_cue_is_shorter_than_200_ms():
    for name, filename in sfx_assets.FILES.items():
        path = AUDIO_DIR / filename
        assert path.is_file(), f"{filename} exists"
        seconds = sfx_assets.duration_seconds(path)
        assert seconds < 0.2, f"{filename} is {seconds:.3f}s, under 200 ms"


def test_the_cues_are_plain_16_bit_mono_wav():
    for filename in sfx_assets.FILES.values():
        with wave.open(str(AUDIO_DIR / filename), "rb") as handle:
            assert handle.getnchannels() == 1, filename
            assert handle.getsampwidth() == 2, filename
            assert handle.getframerate() == sfx_assets.SAMPLE_RATE, filename


def test_the_cues_are_audible_but_never_clip():
    for filename in sfx_assets.FILES.values():
        with wave.open(str(AUDIO_DIR / filename), "rb") as handle:
            samples = _samples(handle.readframes(handle.getnframes()))
        peak = max(abs(value) for value in samples)
        assert peak > 16000, f"{filename} carries a real tone"
        assert peak < 32767, f"{filename} does not clip"


def test_the_assets_are_the_synthesised_ones():
    """A downloaded or hand-edited asset fails here."""
    for name, filename in sfx_assets.FILES.items():
        with wave.open(str(AUDIO_DIR / filename), "rb") as handle:
            stored = _samples(handle.readframes(handle.getnframes()))
        rendered = sfx_assets.render(name)
        assert len(stored) == len(rendered), filename
        # libm differences between platforms move a sample by a unit or two.
        drift = max(abs(a - b) for a, b in zip(stored, rendered))
        assert drift <= 4, f"{filename} differs from the generator by {drift}"

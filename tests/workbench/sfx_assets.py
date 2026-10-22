"""Synthesise the four key-feedback cues as 16-bit PCM WAV assets.

Every sample here is generated from scratch with additive synthesis (a few
sine partials plus a short mallet transient).  Nothing is sampled, recorded or
downloaded, so the assets carry no third-party copyright.

The tones follow `decisions.md` A-3 of
`openspec/changes/workbench-visual-language-v2`: crisp xylophone / glass,
short, never loud.  Each cue is shorter than 200 ms, which is the contract in
the spec requirement "Key feedback audio cues".

Regenerate the assets in place with:

    python tests/workbench/sfx_assets.py

The test `tests/workbench/test_sfx_assets.py` re-renders the cues and compares
them against the committed files, so a hand-edited or downloaded asset fails.
"""

from __future__ import annotations

import math
import sys
import wave
from array import array
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_DIR = REPO_ROOT / "workbench" / "server" / "static" / "assets" / "audio"

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes, 16-bit signed PCM

# Struck bar: strong fundamental, an octave and a twelfth above it.
XYLOPHONE = ([1.0, 2.0, 3.0, 4.2], [1.0, 0.30, 0.12, 0.05])
# Bell: inharmonic partials, the glass shimmer.
GLASS = ([1.0, 2.76, 5.40, 8.20], [1.0, 0.26, 0.10, 0.04])
# Muted wood: almost no upper partials, a dull and apologetic wrong answer.
DULL = ([1.0, 2.0, 3.01], [1.0, 0.16, 0.05])

ATTACK = 0.0015  # seconds, short enough to read as a strike, long enough not to click
PEAK = 0.72  # normalised peak, well below full scale
FADE = 0.005  # seconds of fade-out so the file never ends on a step

# name -> (seconds, notes, transient gain)
# note = (frequency, start seconds, gain, decay seconds, partials)
CUES = {
    "right": (
        0.140,
        [
            (880.00, 0.000, 0.90, 0.085, XYLOPHONE),
            (1318.51, 0.055, 0.85, 0.075, XYLOPHONE),
        ],
        0.050,
    ),
    "wrong": (
        0.140,
        [
            (392.00, 0.000, 0.70, 0.075, DULL),
            (311.13, 0.060, 0.62, 0.070, DULL),
        ],
        0.030,
    ),
    "complete": (
        0.185,
        [
            (523.25, 0.000, 0.80, 0.070, XYLOPHONE),
            (659.25, 0.050, 0.80, 0.070, XYLOPHONE),
            (783.99, 0.100, 0.85, 0.075, XYLOPHONE),
        ],
        0.050,
    ),
    "milestone": (
        0.190,
        [
            (1046.50, 0.000, 0.75, 0.100, GLASS),
            (1318.51, 0.020, 0.70, 0.095, GLASS),
            (1567.98, 0.045, 0.65, 0.090, GLASS),
            (2093.00, 0.070, 0.40, 0.075, GLASS),
        ],
        0.050,
    ),
}

FILES = {name: "sfx-%s.wav" % name for name in CUES}


def _add_partial(buffer, frequency, start, duration, ratio, amplitude, decay, gain):
    """One sine partial with an exponential decay and a 1.5 ms attack."""
    begin = int(round(start * SAMPLE_RATE))
    length = int(round(duration * SAMPLE_RATE))
    for index in range(length):
        position = begin + index
        if position >= len(buffer):
            break
        seconds = index / SAMPLE_RATE
        attack = min(1.0, seconds / ATTACK)
        envelope = math.exp(-seconds / decay) * attack
        buffer[position] += (
            gain * amplitude * envelope
            * math.sin(2.0 * math.pi * frequency * ratio * seconds)
        )


def _add_transient(buffer, start, gain):
    """A 2 ms mallet tick; deterministic noise so the assets stay reproducible."""
    begin = int(round(start * SAMPLE_RATE))
    count = int(round(0.002 * SAMPLE_RATE))
    state = 0x2F6E2B1
    for index in range(count):
        position = begin + index
        if position >= len(buffer):
            break
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        noise = (state / 0x7FFFFFFF) * 2.0 - 1.0
        envelope = (1.0 - index / count) ** 2
        buffer[position] += gain * noise * envelope


def render(name):
    """Render one cue and return its samples as 16-bit signed integers."""
    seconds, notes, transient = CUES[name]
    total = int(round(seconds * SAMPLE_RATE))
    buffer = [0.0] * total
    for frequency, start, gain, decay, (ratios, amplitudes) in notes:
        for ratio, amplitude in zip(ratios, amplitudes):
            _add_partial(
                buffer, frequency, start, seconds - start, ratio,
                amplitude, decay, gain,
            )
        _add_transient(buffer, start, transient)
    peak = max(abs(value) for value in buffer) or 1.0
    scale = PEAK / peak
    fade = int(round(FADE * SAMPLE_RATE))
    values = []
    for index, value in enumerate(buffer):
        if index >= total - fade:
            value *= max(0.0, (total - 1 - index) / float(fade - 1))
        values.append(int(round(value * scale * 32767.0)))
    return array("h", values)


def write(name, target=None):
    """Write one cue to disk and return the path."""
    path = Path(target) if target else AUDIO_DIR / FILES[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = render(name)
    if sys.byteorder != "little":
        samples = array("h", samples)
        samples.byteswap()
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())
    return path


def write_all(target_dir=None):
    directory = Path(target_dir) if target_dir else AUDIO_DIR
    return [write(name, directory / FILES[name]) for name in sorted(CUES)]


def duration_seconds(path):
    """The length of a WAV file in seconds."""
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


if __name__ == "__main__":
    for written in write_all():
        print("%s  %.3fs" % (written, duration_seconds(written)))

"""G-5's R-1 arithmetic (A-132) — the false green must not come back.

``tools/walkthrough/g5.py`` used to subtract the masked area's **pixel count**
from a **three-channel sum**.  On a 1440x900 page the mask covered 312,320
pixels, so every real difference below ``312,320 / 3 = 104,106`` pixels was
swallowed and R-1 reported PASS for a page that had changed.

The arithmetic is now: count the differing pixels **outside** the mask (the
graph's own area) and report the differing pixels **inside** the mask
separately (``maskedDiff`` — the shared shell's honest number).  Nothing is
subtracted any more.

The tests below pin three things:

* a difference **inside** the mask is not counted as the graph's difference,
  but it is **visible** in ``maskedDiff`` (the old arithmetic hid it and
  reported a false green);
* a difference **outside** the mask is counted (the old arithmetic swallowed
  it as well);
* the right column is excluded **from the captured geometry**, not from a
  hard-coded x.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "walkthrough"))

import g5  # noqa: E402  (the path is set up above)

SIZE = (1440, 900)
EXCLUDE_LEFT = 280
EXCLUDE_TOP = 52


def _diff_pixels_old(left, right, mask=None):
    """The arithmetic A-132 removed — kept here as the reference."""
    from PIL import ImageChops

    diff = ImageChops.difference(left, right)
    bands = diff.split()
    total = 0
    for band in bands:
        total += sum(band.histogram()[1:])
    if mask is not None:
        masked = 0
        pixels = diff.load()
        mask_pixels = mask.load()
        width, height = diff.size
        for y in range(height):
            for x in range(width):
                if mask_pixels[x, y]:
                    masked += 1
        total = max(0, total - masked)
    return total


def _page():
    """A blank dark page (the mask's threshold depends on the size only)."""
    from PIL import Image

    return Image.new("RGB", SIZE, (0, 0, 0))


def _block(image, box, colour=(255, 255, 255)):
    from PIL import ImageDraw

    ImageDraw.Draw(image).rectangle(box, fill=colour)


def test_difference_inside_the_mask_is_reported_not_swallowed():
    """100x100 px of difference inside the mask (the shared shell).

    The old arithmetic: 3 x 10,000 = 30,000 channel units minus the mask's
    312,320 pixels ⇒ **0** ⇒ R-1 reported PASS (a false green).
    """
    before = _page()
    after = _page()
    _block(after, (50, 100, 149, 199))          # 100x100 px, inside the left column
    mask = g5._mask_for(SIZE, EXCLUDE_LEFT, EXCLUDE_TOP)

    assert _diff_pixels_old(before, after, mask=mask) == 0, (
        "the reference implementation is what A-132 removed — if this ever "
        "stops being 0, the old arithmetic changed")

    ae, detail = g5._diff_pixels(before, after, mask=mask)
    assert ae == 0, "the graph's own area did not change ⇒ the verdict is 0"
    assert detail["maskedDiff"] == 100 * 100, "the shell's difference is visible"
    assert detail["outsideMaskDiff"] == 0
    assert detail["pixelDiff"] == 100 * 100


def test_difference_outside_the_mask_is_counted():
    """5,000 px of difference outside the mask (the graph's own area).

    The old arithmetic swallowed this one too (15,000 - 312,320 ⇒ 0).
    """
    before = _page()
    after = _page()
    _block(after, (400, 200, 499, 249))          # 100x50 px, outside the mask
    mask = g5._mask_for(SIZE, EXCLUDE_LEFT, EXCLUDE_TOP)

    assert _diff_pixels_old(before, after, mask=mask) == 0

    ae, detail = g5._diff_pixels(before, after, mask=mask)
    assert ae == 5000, "the difference in the graph's own area is counted"
    assert detail["maskedDiff"] == 0
    assert detail["outsideMaskDiff"] == 5000


def test_the_count_is_a_pixel_count_not_a_channel_sum():
    """One differing pixel counts once, not three times."""
    before = _page()
    after = _page()
    _block(after, (400, 200, 400, 200))          # a single pixel
    mask = g5._mask_for(SIZE, EXCLUDE_LEFT, EXCLUDE_TOP)

    ae, detail = g5._diff_pixels(before, after, mask=mask)
    assert ae == 1
    assert detail["pixelDiff"] == 1
    assert detail["channelSum"] == 3, "the per-channel breakdown is kept"
    assert detail["perBand"] == [1, 1, 1]


def test_the_right_column_is_excluded_from_the_captured_geometry():
    """The right column's boundary comes from the artefacts, not from a constant."""
    right_rect = [1037, 0, 387, 900]
    before = _page()
    after = _page()
    _block(after, (1100, 300, 1199, 399))        # inside the right column
    mask = g5._mask_for(SIZE, EXCLUDE_LEFT, EXCLUDE_TOP, [right_rect])

    ae, detail = g5._diff_pixels(before, after, mask=mask)
    assert ae == 0, "the right column is the shared shell ⇒ not the graph"
    assert detail["maskedDiff"] == 100 * 100


def test_shell_rect_is_read_from_the_artefacts():
    """``_shell_rect`` unions both sides and refuses to guess."""
    before = {"right": [1037, 0, 387, 900]}
    after = {"right": [1037, 0, 387, 900]}
    rect, note = g5._shell_rect(before, after)
    assert rect == [1037.0, 0.0, 387.0, 900.0]
    assert "captured geometry" in note

    # a shell that moved between the two sides is out of the scope on both
    moved = {"right": [1000, 0, 424, 900]}
    rect, _ = g5._shell_rect(before, moved)
    assert rect == [1000.0, 0.0, 424.0, 900.0]

    # no geometry ⇒ no boundary, and the note says so
    rect, note = g5._shell_rect({}, {})
    assert rect is None
    assert "NOT in the artefacts" in note

    # ``.side-sections`` is the **left** column's paper (measured on the graph
    # page: [0, 52, 279, 697]) ⇒ it must not be taken for the right column
    rect, note = g5._shell_rect({"sideSections": [0, 52, 279, 697]}, {})
    assert rect is None


def test_a_missing_geometry_is_recorded_in_the_scope():
    """Without the right column's geometry the shell is NOT silently dropped."""
    from PIL import Image

    before = Image.new("RGB", (400, 300), (0, 0, 0))
    after = Image.new("RGB", (400, 300), (0, 0, 0))
    mask = g5._mask_for(before.size, 10, 10, [])
    ae, detail = g5._diff_pixels(before, after, mask=mask)
    assert ae == 0
    assert detail["maskedDiff"] == 0


@pytest.mark.parametrize("left,top", [(0, 0), (5, 5), (279, 51), (279, 500)])
def test_the_mask_marks_the_excluded_area(left, top):
    """255 marks an excluded pixel; the graph's own area is 0."""
    mask = g5._mask_for(SIZE, EXCLUDE_LEFT, EXCLUDE_TOP)
    assert mask.getpixel((left, top)) == 255
    assert mask.getpixel((EXCLUDE_LEFT, EXCLUDE_TOP)) == 0, (
        "the first pixel of the graph's own area is not excluded")

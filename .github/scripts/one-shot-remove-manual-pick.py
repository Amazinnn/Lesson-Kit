from pathlib import Path

flow_path = Path("workbench/server/static/practice-flow.js")
flow = flow_path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global flow
    count = flow.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    flow = flow.replace(old, new, 1)


flow = flow.replace('    var INCLUDE_KEY = "wb_practice_include_" + WS;\n', '')
flow = flow.replace('      var includeIds = load(INCLUDE_KEY, null);\n', '')
flow = flow.replace('      if (includeIds && includeIds.length) pullBody.include_ids = includeIds.slice();\n', '')
flow = flow.replace('        sessionStorage.removeItem(INCLUDE_KEY);\n', '')

replace_once(
    '''      if (includeIds && includeIds.length) {
        pullBody.include_ids = (pullBody.include_ids || []).concat(
          includeIds.filter(function (id) {
            return (pullBody.include_ids || []).indexOf(id) < 0;
          }));
      }
''',
    '',
    "legacy include merge",
)

replace_once(
    '''    var filterState = load(FILTER_KEY, null)
      || { source_kinds: [], origin_kinds: [], exam_years: [], docs: [], picked: {} };
    if (!filterState.picked) filterState.picked = {};
''',
    '''    var filterState = load(FILTER_KEY, null)
      || { source_kinds: [], origin_kinds: [], exam_years: [], docs: [] };
    // Old saved picker state is discarded; source dimensions still constrain Paper assembly.
    if (filterState.picked) delete filterState.picked;
''',
    "filter state",
)

replace_once(
    '''      return filterState.source_kinds.length + filterState.origin_kinds.length
        + filterState.exam_years.length
        + filterState.docs.length + Object.keys(filterState.picked).length;
''',
    '''      return filterState.source_kinds.length + filterState.origin_kinds.length
        + filterState.exam_years.length + filterState.docs.length;
''',
    "filter badge",
)

replace_once(
    '''      if (Object.keys(dimensions).length) pullBody.filters = dimensions;
      var pickedIds = Object.keys(filterState.picked || {});
      if (pickedIds.length) pullBody.include_ids = pickedIds;
''',
    '''      if (Object.keys(dimensions).length) pullBody.filters = dimensions;
''',
    "picked ids injection",
)

replace_once(
    '''        + filterDimension("exam_years", "考查年份", filterFacets.exam_years || [])
        + filterDimension("docs", "来源文档", filterFacets.docs || [])
        + "<div class='filter-dimension'><h3>搜索选题</h3>"
        + "<div class='filter-search'>"
        + "<input id='filter-search-stem' type='search' "
        + "placeholder='题干关键词（空格分隔）'>"
        + "<input id='filter-search-source' type='search' "
        + "placeholder='来源关键词（空格分隔）'>"
        + "<button id='filter-search-go' class='outline sm'>搜</button></div>"
        + "<div id='filter-search-results' class='filter-search-results'></div></div>"
        + "<div class='filter-actions'>"
''',
    '''        + filterDimension("exam_years", "考查年份", filterFacets.exam_years || [])
        + filterDimension("docs", "来源文档", filterFacets.docs || [])
        + "<div class='filter-actions'>"
''',
    "manual picker markup",
)

start = flow.find('      var searchGo = filterPopup.querySelector("#filter-search-go");')
end = flow.find('      var clear = filterPopup.querySelector("#filter-clear");', start)
if start < 0 or end < 0:
    raise SystemExit("manual picker handlers: block not found")
flow = flow[:start] + flow[end:]

replace_once(
    '''        filterState = {
          source_kinds: [], origin_kinds: [], exam_years: [], docs: [], picked: {},
        };
''',
    '''        filterState = {
          source_kinds: [], origin_kinds: [], exam_years: [], docs: [],
        };
''',
    "filter clear",
)

# `filterState.picked` is allowed only in the one migration line that discards
# stale browser storage; no live read/write path may remain.
for token in (
    "INCLUDE_KEY",
    "wb_practice_include_",
    "include_ids",
    "data-picked-id",
    "搜索选题",
):
    if token in flow:
        raise SystemExit(f"practice-flow still contains retired token: {token}")
if flow.count("filterState.picked") != 2:
    # one condition + one delete on the same migration statement
    raise SystemExit("unexpected live filterState.picked usage remains")
flow_path.write_text(flow, encoding="utf-8")

wb_path = Path("workbench/server/static/workbench.js")
wb = wb_path.read_text(encoding="utf-8")
line = '  var INCLUDE_KEY = "wb_practice_include_" + WS;\n'
if wb.count(line) != 1:
    raise SystemExit(f"workbench INCLUDE_KEY expected once, got {wb.count(line)}")
wb = wb.replace(line, "", 1)
if "wb_practice_include_" in wb:
    raise SystemExit("workbench.js still contains retired include storage")
wb_path.write_text(wb, encoding="utf-8")

test_path = Path("tests/workbench/test_retired_manual_problem_include.py")
test = test_path.read_text(encoding="utf-8")
marker = "class RetiredManualPickerStaticTests"
if marker not in test:
    test += '''\n\nclass RetiredManualPickerStaticTests(unittest.TestCase):
    def test_browser_bundle_has_no_manual_problem_picker_or_include_state(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        flow = (root / "workbench/server/static/practice-flow.js").read_text(encoding="utf-8")
        workbench = (root / "workbench/server/static/workbench.js").read_text(encoding="utf-8")

        for retired in (
            "wb_practice_include_", "include_ids", "data-picked-id", "搜索选题",
        ):
            self.assertNotIn(retired, flow)
        self.assertNotIn("wb_practice_include_", workbench)
        self.assertNotIn("Object.keys(filterState.picked", flow)
        self.assertNotIn("filterState.picked[", flow)
'''
    test_path.write_text(test, encoding="utf-8")

Path(".github/workflows/one-shot-remove-manual-pick.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-remove-manual-pick.py").unlink()

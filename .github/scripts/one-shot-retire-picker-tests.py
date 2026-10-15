from pathlib import Path

api_path = Path("tests/workbench/test_api.py")
api = api_path.read_text(encoding="utf-8")
old_api = '''    def test_pull_include_ids_restricts_scope(self):
        status, data = self.post("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "weak",
            "include_ids": ["dmath-ch06-prob-001"],
        })
        self.assertEqual(status, 200)
        self.assertEqual(
            [p["problem_id"] for p in data["problems"]], ["dmath-ch06-prob-001"])

    def test_pull_include_ids_with_all_mode_rejected(self):
        status, data = self.post_error("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "all",
            "include_ids": ["dmath-ch06-prob-001"],
        })
        self.assertEqual(status, 400)

'''
new_api = '''    def test_pull_include_ids_is_retired_for_browser_practice(self):
        status, data = self.post_error("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "weak",
            "include_ids": ["dmath-ch06-prob-001"],
        })
        self.assertEqual(status, 400)
        self.assertIn("include_ids is retired", data["error"])
        self.assertIn("compose a paper", data["error"])

'''
if api.count(old_api) != 1:
    raise SystemExit(f"API legacy include test block count={api.count(old_api)}")
api_path.write_text(api.replace(old_api, new_api, 1), encoding="utf-8")

ui_path = Path("tests/workbench/workbench_ui_interactions.test.js")
ui = ui_path.read_text(encoding="utf-8")
start_marker = 'test("a pull carries the saved dimensions and the picked ids", async () => {'
end_marker = 'test("micro quiz renders yes/no options and grades the objective answer", async () => {'
start = ui.find(start_marker)
end = ui.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("legacy picker test range not found")
replacement = '''test("a pull carries source dimensions and ignores legacy picked-problem state", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  const storage = new FakeStorage({
    wb_practice_filters_v2_alpha: JSON.stringify({
      source_kinds: ["final"],
      origin_kinds: ["source_problem", "adapted_problem"],
      exam_years: ["2023-2024秋冬"],
      docs: ["题库/final·A.md"],
      picked: { "prob-7": "retired legacy state" },
    }),
  });
  runWorkbench({
    storage,
    elements,
    fetch: (url, options) => {
      calls.push({ url, body: options && options.body ? JSON.parse(options.body) : null });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      if (url.endsWith("/pull-facets")) return jsonResponse({
        source_kinds: [{ value: "final", count: 9 }],
        origin_kinds: [
          { value: "source_problem", count: 4 },
          { value: "adapted_problem", count: 3 },
        ],
        exam_years: [{ value: "2023-2024秋冬", count: 5 }],
        docs: [{ value: "题库/final·A.md", count: 6 }],
      });
      return jsonResponse({ problems: [] });
    },
  });

  // Four dimensions contribute five selected values; retired picked state is ignored.
  assert.equal(elements["filter-count"].textContent, "5");
  elements["filter-launch"].click();
  await flush();
  await flush();
  const popup = elements["filter-popup"].innerHTML;
  assert.ok(!popup.includes("搜索选题"), popup);
  assert.ok(!popup.includes("filter-search-stem"), popup);
  assert.ok(!popup.includes("filter-search-source"), popup);

  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.ok(pull, "starting practice must pull");
  assert.deepEqual(pull.body.filters, {
    source_kinds: ["final"],
    origin_kinds: ["source_problem", "adapted_problem"],
    exam_years: ["2023-2024秋冬"],
    docs: ["题库/final·A.md"],
  });
  assert.equal(Object.hasOwn(pull.body, "include_ids"), false);
});

'''
ui = ui[:start] + replacement + ui[end:]
for retired_title in (
    "the two search boxes send one parameter each and pick by problem id",
    "a search with both boxes empty clears the result list instead of listing the pool",
    "a pull carries the saved dimensions and the picked ids",
):
    if retired_title in ui:
        raise SystemExit(f"retired UI test still present: {retired_title}")
ui_path.write_text(ui, encoding="utf-8")

Path(".github/workflows/one-shot-retire-picker-tests.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-retire-picker-tests.py").unlink()

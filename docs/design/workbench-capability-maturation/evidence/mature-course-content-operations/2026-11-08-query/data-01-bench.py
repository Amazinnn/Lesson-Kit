"""DATA-01 / task 2.1: 100 knowledge-point queries on a realistic pool, p95 <= 1s."""
import json, os, random, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tmp" / "accept"))
from p3_f1 import build_course  # reuse fixture builder

from workbench import registry
from workbench.data import content
from workbench.data.pool import Pool

work = Path(tempfile.mkdtemp(prefix="wp02-bench-"))
root = work / "course"
db = build_course(root)
conn = sqlite3.connect(db)
types = ("concept-property", "method-modeling", "formula-calculation", "memory-recall")
for index in range(1, 501):
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body, knowledge_type, source_location, importance)"
        " VALUES (?,?,?,?,?,'core')",
        (f"dmath-ch{1 + index % 8:02d}-kp-{900 + index:03d}", f"Point {index}",
         "body text about counting and graphs " * 3 + f"token{index}",
         types[index % len(types)], f"Rosen {index}"))
for index in range(1, 2001):
    conn.execute(
        "INSERT INTO problems (problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
        " VALUES (?,?,?,'solution','calculation','textbook')",
        (f"dmath-ch{1 + index % 8:02d}-prob-{9000 + index}", json.dumps(
            [f"dmath-ch{1 + index % 8:02d}-kp-{900 + 1 + index % 500:03d}"]), f"question {index}"))
conn.commit(); conn.close()

os.environ["LESSONKIT_WB_HOME"] = str(work / "registry")
registry.register(name="bench", path=root, db="pool/course.db", course="dmath", chapter="")
pool = Pool(root, db, "dmath", "")
random.seed(11)
timings = []
for _ in range(100):
    kind = random.choice(types)
    chapter = f"ch{1 + random.randrange(8):02d}"
    started = time.perf_counter()
    hits = content.knowledge_query(pool, types=[kind], chapter=chapter, text="counting")
    timings.append(time.perf_counter() - started)
timings.sort()
related = []
for _ in range(25):
    kp = f"dmath-ch{1 + random.randrange(8):02d}-kp-{900 + 1 + random.randrange(500):03d}"
    started = time.perf_counter()
    content.related_problems(pool, [kp, kp])
    related.append(time.perf_counter() - started)
related.sort()
result = {"queries": 100, "kps": 512, "problems": 2024,
          "query_p50": round(timings[49], 4), "query_p95": round(timings[94], 4),
          "query_max": round(timings[-1], 4),
          "related_runs": 25, "related_p95": round(related[23], 4),
          "threshold_seconds": 1.0,
          "verdict": "PASS" if timings[94] <= 1.0 else "FAIL",
          "sample_hits": len(hits)}
(ROOT / "tmp/accept/wp02-query-report.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
pool.close()

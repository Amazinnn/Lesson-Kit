import asyncio, pathlib, re
from playwright.async_api import async_playwright

ROOT = pathlib.Path("workbench/server/static/assets")
OUT = pathlib.Path("tmp/asset-shots"); OUT.mkdir(parents=True, exist_ok=True)
files = sorted(ROOT.glob("empty/*.svg")) + sorted(ROOT.glob("motion/*.svg"))
cells = ""
for f in files:
    raw = f.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw).strip()
    raw = re.sub(r'width="[^"]*"\s+height="[^"]*"', 'width="180" height="180"', raw, count=1)
    cells += (f'<figure>{raw}<figcaption>{f.parent.name}/{f.name} '
              f'({f.stat().st_size}B)</figcaption></figure>')
html = f"""<!doctype html><meta charset=utf-8>
<style>
 body{{margin:0;background:#fdf8ef;font:13px/1.5 -apple-system,"Segoe UI",sans-serif;padding:16px}}
 .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
 figure{{margin:0;background:#fffdf7;border:1px solid #e6dcc4;border-radius:12px;padding:10px;text-align:center}}
 figure svg{{display:block;margin:0 auto}}
 figcaption{{color:#6b6459;margin-top:6px;font-size:12px}}
</style><div class=grid>{cells}</div>"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1000, "height": 900}, device_scale_factor=2)
        await pg.set_content(html)
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(OUT / "grid.png"), full_page=True)
        await b.close()
asyncio.run(main())
print("ok", OUT / "grid.png")

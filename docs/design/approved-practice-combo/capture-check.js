async (page) => {
  const results = [];
  const base = 'http://127.0.0.1:3920/docs/design/approved-practice-combo/preview.html';
  for (const width of [680, 375, 250]) {
    await page.setViewportSize({width, height:800});
    const golden = new Map();
    for (const source of [true, false]) {
      await page.goto(base + (source ? '?source' : ''));
      await page.evaluate(() => window.ready);
      for (const age of [400, 1000, 1750]) {
        await page.evaluate(t => window.paint(t), age);
        const buffer = await page.screenshot();
        if (source) golden.set(age, buffer);
        else {
          const matches = buffer.equals(golden.get(age));
          results.push({captureWidth:width, cssWidth:await page.evaluate(()=>innerWidth), age, matches});
          if (!matches) throw new Error('Approved Combo differs at '+width+' / '+age);
        }
      }
    }
  }
  return results;
}

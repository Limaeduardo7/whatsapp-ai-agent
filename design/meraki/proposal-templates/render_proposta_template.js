const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const htmlPath = path.resolve('/root/clawd/design/meraki/proposal-templates/proposta_template_exemplo.html');
  const outPng = path.resolve('/root/clawd/design/meraki/proposal-templates/proposta_template_exemplo.png');
  const outPdf = path.resolve('/root/clawd/design/meraki/proposal-templates/proposta_template_exemplo.pdf');

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 2200 } });
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
  await page.screenshot({ path: outPng, fullPage: true });
  await page.pdf({
    path: outPdf,
    format: 'A4',
    printBackground: true,
    margin: { top: '12mm', right: '12mm', bottom: '14mm', left: '12mm' }
  });
  await browser.close();
  console.log('Rendered:', outPng, outPdf);
})();

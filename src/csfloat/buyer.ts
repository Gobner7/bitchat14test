import puppeteer from 'puppeteer';
import { logger } from '../logger.js';

export type BrowserBuyerOptions = {
  cookiesHeader?: string; // Full Cookie header string for csfloat.com domain
};

function parseCookieHeader(cookieHeader: string): { name: string; value: string }[] {
  return cookieHeader
    .split(';')
    .map((kv) => kv.trim())
    .filter(Boolean)
    .map((pair) => {
      const idx = pair.indexOf('=');
      const name = idx === -1 ? pair : pair.slice(0, idx);
      const value = idx === -1 ? '' : pair.slice(idx + 1);
      return { name, value };
    })
    .filter((c) => c.name.toLowerCase() !== 'path' && c.name.toLowerCase() !== 'domain');
}

export async function buyListingWithBrowser(listingUrl: string, options: BrowserBuyerOptions): Promise<boolean> {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    if (options.cookiesHeader) {
      const cookies = parseCookieHeader(options.cookiesHeader).map((c) => ({
        name: c.name,
        value: c.value,
        domain: 'csfloat.com',
        httpOnly: false,
        secure: true,
        path: '/',
      }));
      await page.setCookie(...cookies);
    }
    await page.goto(listingUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    // Try to click Buy button (various UI variants)
    const buyButtonSelectors = [
      'button:has-text("Buy")',
      'button[aria-label="Buy"]',
      'text/Buy',
      'button:has-text("Purchase")',
      'text/Purchase',
    ];
    let clicked = false;
    for (const sel of buyButtonSelectors) {
      try {
        await page.waitForSelector(sel, { timeout: 5000 });
        await page.click(sel);
        clicked = true;
        break;
      } catch {}
    }
    if (!clicked) {
      logger.warn('Buy button not found');
      return false;
    }
    // Confirm modal
    const confirmSelectors = [
      'button:has-text("Confirm")',
      'text/Confirm',
      'button:has-text("Pay")',
      'text/Pay',
    ];
    for (const sel of confirmSelectors) {
      try {
        await page.waitForSelector(sel, { timeout: 8000 });
        await page.click(sel);
        break;
      } catch {}
    }
    // Wait for success indicator
    await page.waitForFunction(
      () => {
        return (
          document.body.innerText.toLowerCase().includes('purchase successful') ||
          document.body.innerText.toLowerCase().includes('purchased') ||
          document.body.innerText.toLowerCase().includes('successfully purchased')
        );
      },
      { timeout: 20000 },
    );
    return true;
  } catch (error) {
    logger.error({ err: String(error) }, 'Failed to buy listing via browser');
    return false;
  } finally {
    await browser.close();
  }
}


import axios from 'axios';
import * as cheerio from 'cheerio';
import { logger } from '../logger.js';
import type { MarketListing } from '../types.js';

export async function scrapeRecentListings(limit: number = 50): Promise<MarketListing[]> {
  try {
    const url = 'https://csfloat.com/market?sort=recent';
    const { data: html } = await axios.get<string>(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 20000,
    });
    const $ = cheerio.load(html);
    const results: MarketListing[] = [];
    $('a[href^="/listing/"]').each((_: number, el: any) => {
      if (results.length >= limit) return false;
      const href = $(el).attr('href');
      const listingId = href?.split('/').pop() || '';
      // Try to find surrounding item name and price
      const card = $(el).closest('div');
      const name = card.find('div:contains("|")').first().text().trim() || $(el).text().trim();
      const priceText = (card.find('[class*="price"]').first().text().trim() || card.find(':contains("$")').first().text().trim());
      const price = Number(priceText.replace(/[^0-9.]/g, ''));
      const priceCents = Number.isFinite(price) ? Math.round(price * 100) : 0;
      if (!listingId || !name || priceCents <= 0) return;
      results.push({
        listingId,
        marketHashName: name,
        priceCents,
        floatValue: null,
        url: `https://csfloat.com/listing/${listingId}`,
      });
    });
    return results;
  } catch (error) {
    logger.error({ err: String(error) }, 'Failed to scrape CSFloat market');
    return [];
  }
}


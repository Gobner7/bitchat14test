import axios from 'axios';
import { logger } from '../logger.js';

export async function getSteamPriceCents(marketHashName: string): Promise<number | null> {
  try {
    const params = new URLSearchParams({
      appid: '730',
      market_hash_name: marketHashName,
      currency: '1', // USD
    });
    const url = `https://steamcommunity.com/market/priceoverview/?${params.toString()}`;
    const { data } = await axios.get(url, { timeout: 15000, headers: { 'User-Agent': 'Mozilla/5.0' } });
    if (!data || data.success !== true) return null;
    // data.lowest_price like '$12.34'
    const priceStr: string | undefined = data.median_price || data.lowest_price || data.lowest_price;
    if (!priceStr) return null;
    const price = Number(String(priceStr).replace(/[^0-9.]/g, ''));
    if (Number.isFinite(price)) return Math.round(price * 100);
    return null;
  } catch (error) {
    logger.warn({ err: String(error), marketHashName }, 'Steam price fetch failed');
    return null;
  }
}


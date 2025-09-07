import axios from 'axios';
import { logger } from '../logger.js';

export async function getCsgobackpackPriceCents(marketHashName: string): Promise<number | null> {
  try {
    const url = `https://csgobackpack.net/api/GetItemPrice/?currency=USD&id=${encodeURIComponent(marketHashName)}`;
    const { data } = await axios.get(url, { timeout: 15000 });
    // Expected data: { success: true, currency: 'USD', average_price: '12.34', median_price: '12.00', ... }
    if (!data || data.success !== true) return null;
    const priceStr: string | undefined = data.median_price || data.average_price;
    if (!priceStr) return null;
    const price = Number(String(priceStr).replace(/[^0-9.]/g, ''));
    if (Number.isFinite(price)) return Math.round(price * 100);
    return null;
  } catch (error) {
    logger.warn({ err: String(error), marketHashName }, 'CSGOBACKPACK price fetch failed');
    return null;
  }
}


import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { logger } from '../logger.js';
import type { MarketListing, PurchaseResult } from '../types.js';

// NOTE: CSFloat does not publish official public buy/list endpoints in docs accessible here.
// This client provides read-only listing fetch via their public market pages API if available,
// and leaves purchase/list operations as no-ops unless a session cookie is supplied for browser automation.

export class CSFloatClient {
  private http: AxiosInstance;
  private sessionCookie: string | undefined;

  constructor(options?: { sessionCookie?: string }) {
    this.sessionCookie = options?.sessionCookie;
    this.http = axios.create({
      baseURL: 'https://csfloat.com',
      timeout: 20000,
      headers: {
        'User-Agent': 'Mozilla/5.0',
      },
    });
  }

  async fetchRecentListings(params?: { limit?: number; minPriceCents?: number; maxPriceCents?: number }): Promise<MarketListing[]> {
    try {
      // Public listings endpoint used by site. If blocked, fallback to scrape.
      const url = '/api/v1/market/recent';
      const { data } = await this.http.get(url, { params: { limit: params?.limit ?? 50 } });
      if (!data || !Array.isArray(data)) return [];
      const listings: MarketListing[] = data
        .map((l: any) => {
          const priceCents = Math.round((l?.price ?? 0) * 100) || 0;
          return {
            listingId: String(l?.id ?? ''),
            marketHashName: String(l?.item?.name ?? l?.market_hash_name ?? ''),
            priceCents,
            floatValue: typeof l?.item?.float === 'number' ? l.item.float : null,
            url: `https://csfloat.com/listing/${l?.id}`,
          } as MarketListing;
        })
        .filter((x: MarketListing) => x.listingId && x.marketHashName && x.priceCents > 0);

      return listings;
    } catch (error) {
      logger.warn({ err: String(error) }, 'Failed to fetch CSFloat recent listings');
      return [];
    }
  }

  async purchaseListing(): Promise<PurchaseResult> {
    if (!this.sessionCookie) {
      return { success: false, message: 'No CSFloat session cookie provided' };
    }
    // Placeholder: purchase would require authenticated actions. You can wire this to a browser automation flow.
    return { success: false, message: 'Direct API purchase not implemented in this client' };
  }
}


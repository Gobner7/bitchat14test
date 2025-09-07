import { loadConfig } from './config.js';
import { logger } from './logger.js';
import { BotDatabase } from './db.js';
import { scrapeRecentListings } from './csfloat/scraper.js';
import { getReferencePriceCents } from './pricing/index.js';
import { evaluateDeal, isWhitelistedItem } from './strategy/engine.js';
import { v4 as uuidv4 } from 'uuid';
import PQueue from 'p-queue';
import { buyListingWithBrowser } from './csfloat/buyer.js';

export async function runTraderLoop() {
  const cfg = loadConfig();
  const db = new BotDatabase('/workspace/data/bot.sqlite');
  const queue = new PQueue({ concurrency: 2, interval: 1000, intervalCap: 4 });

  logger.info({ cfg }, 'Starting trader loop');
  // Main loop
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const listings = await scrapeRecentListings(40);
      for (const listing of listings) {
        if (!isWhitelistedItem(listing.marketHashName, cfg.whitelistItems, cfg.blacklistItems)) {
          continue;
        }
        if (db.hasSeenListing(listing.listingId)) continue;
        db.markListingSeen(listing.listingId, listing.marketHashName, listing.priceCents);
        queue.add(async () => {
          const { priceCents: refPrice } = await getReferencePriceCents(listing.marketHashName, cfg.priceSource);
          if (!refPrice) return;
          const evalResult = evaluateDeal(cfg, listing.priceCents, refPrice);
          if (!evalResult.isDeal) return;
          const tradeId = uuidv4();
          db.insertTrade({
            id: tradeId,
            listingId: listing.listingId,
            marketHashName: listing.marketHashName,
            buyPriceCents: listing.priceCents,
            targetSellPriceCents: evalResult.targetSellPriceCents,
            roiPct: evalResult.roiPct,
            status: 'pending',
            createdAt: new Date().toISOString(),
          });
          logger.info({ listing, evalResult }, 'Attempting purchase');
          const ok = await buyListingWithBrowser(listing.url, {
            cookiesHeader: process.env.CSFLOAT_COOKIES ?? '',
          });
          if (ok) {
            db.updateTradeStatus(tradeId, 'bought');
            logger.info({ listing }, 'Purchased successfully');
          } else {
            db.updateTradeStatus(tradeId, 'failed');
          }
        });
      }
      await queue.onIdle();
    } catch (error) {
      logger.error({ err: String(error) }, 'Trader loop error');
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
}


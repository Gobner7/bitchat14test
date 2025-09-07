import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { logger } from './logger.js';

export type TradeStatus = 'pending' | 'bought' | 'listed' | 'sold' | 'failed';

export type TradeRecord = {
  id: string;
  listingId: string;
  marketHashName: string;
  buyPriceCents: number;
  targetSellPriceCents: number | null;
  roiPct: number | null;
  status: TradeStatus;
  createdAt: string;
};

export class BotDatabase {
  private db: Database.Database;

  constructor(dbFilePath: string) {
    const dir = path.dirname(dbFilePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    this.db = new Database(dbFilePath);
    this.db.pragma('journal_mode = WAL');
    this.initialize();
  }

  private initialize() {
    this.db.exec(`
      create table if not exists trades (
        id text primary key,
        listing_id text not null,
        market_hash_name text not null,
        buy_price_cents integer not null,
        target_sell_price_cents integer,
        roi_pct real,
        status text not null,
        created_at text not null
      );
      create table if not exists seen_listings (
        listing_id text primary key,
        market_hash_name text not null,
        price_cents integer not null,
        seen_at text not null
      );
      create table if not exists price_cache (
        market_hash_name text primary key,
        source text not null,
        price_cents integer not null,
        updated_at text not null
      );
      create index if not exists idx_seen_listings_seen_at on seen_listings (seen_at);
    `);
    logger.info('Database initialized');
  }

  markListingSeen(listingId: string, marketHashName: string, priceCents: number) {
    const stmt = this.db.prepare(
      'insert or ignore into seen_listings (listing_id, market_hash_name, price_cents, seen_at) values (?, ?, ?, ?)',
    );
    stmt.run(listingId, marketHashName, priceCents, new Date().toISOString());
  }

  hasSeenListing(listingId: string): boolean {
    const row = this.db.prepare('select 1 from seen_listings where listing_id = ?').get(listingId);
    return !!row;
  }

  upsertPriceCache(marketHashName: string, source: string, priceCents: number) {
    const stmt = this.db.prepare(
      'insert into price_cache (market_hash_name, source, price_cents, updated_at) values (?, ?, ?, ?) on conflict(market_hash_name) do update set source=excluded.source, price_cents=excluded.price_cents, updated_at=excluded.updated_at',
    );
    stmt.run(marketHashName, source, priceCents, new Date().toISOString());
  }

  getCachedPrice(marketHashName: string): { priceCents: number; source: string; updatedAt: string } | null {
    const row = this.db
      .prepare('select price_cents as priceCents, source, updated_at as updatedAt from price_cache where market_hash_name = ?')
      .get(marketHashName) as { priceCents: number; source: string; updatedAt: string } | undefined;
    return row ?? null;
  }

  insertTrade(trade: TradeRecord) {
    const stmt = this.db.prepare(
      'insert into trades (id, listing_id, market_hash_name, buy_price_cents, target_sell_price_cents, roi_pct, status, created_at) values (?, ?, ?, ?, ?, ?, ?, ?)',
    );
    stmt.run(
      trade.id,
      trade.listingId,
      trade.marketHashName,
      trade.buyPriceCents,
      trade.targetSellPriceCents,
      trade.roiPct,
      trade.status,
      trade.createdAt,
    );
  }

  updateTradeStatus(id: string, status: TradeStatus) {
    this.db.prepare('update trades set status = ? where id = ?').run(status, id);
  }
}


import { describe, it, expect } from 'vitest';
import { evaluateDeal } from './engine.js';

describe('evaluateDeal', () => {
  it('flags a deal when ROI exceeds threshold after fees', () => {
    const cfg = {
      csfloatFeePct: 2,
      minRoiPct: 5,
      priceSource: 'steam',
      maxInventoryUsd: 1000,
      whitelistItems: [],
      blacklistItems: [],
    } as any;
    const listing = 800; // $8.00
    const ref = 1000; // $10.00
    const r = evaluateDeal(cfg, listing, ref);
    expect(r.isDeal).toBe(true);
  });
});


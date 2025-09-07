import type { AppConfig } from '../config.js';

export type DealEvaluation = {
  isDeal: boolean;
  roiPct: number;
  targetSellPriceCents: number;
  reason: string | undefined;
};

export function evaluateDeal(
  cfg: AppConfig,
  listingPriceCents: number,
  referencePriceCents: number,
): DealEvaluation {
  const feeMultiplier = 1 - cfg.csfloatFeePct / 100;
  const netSellProceeds = Math.floor(referencePriceCents * feeMultiplier);
  const profitCents = netSellProceeds - listingPriceCents;
  const roiPct = (profitCents / listingPriceCents) * 100;
  const isDeal = roiPct >= cfg.minRoiPct && profitCents > 0;
  return {
    isDeal,
    roiPct,
    targetSellPriceCents: referencePriceCents,
    reason: isDeal ? undefined : 'ROI below threshold or non-profitable',
  };
}

export function isWhitelistedItem(
  marketHashName: string,
  whitelist: string[],
  blacklist: string[],
): boolean {
  if (blacklist.some((b) => marketHashName.includes(b))) return false;
  if (whitelist.length === 0) return true;
  return whitelist.some((w) => marketHashName.includes(w));
}


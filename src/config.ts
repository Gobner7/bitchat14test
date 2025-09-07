import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const EnvSchema = z.object({
  CSFLOAT_API_KEY: z.string().optional(),
  CSFLOAT_SESSION_COOKIE: z.string().optional(),
  CSFLOAT_COOKIES: z.string().optional(),
  STEAM_API_KEY: z.string().optional(),
  PRICE_SOURCE: z.enum(['steam', 'csgobackpack']).default('steam'),
  MIN_ROI_PCT: z
    .string()
    .default('5')
    .transform((v) => Number(v))
    .pipe(z.number().min(0).max(100)),
  MAX_INVENTORY_USD: z
    .string()
    .default('200')
    .transform((v) => Number(v))
    .pipe(z.number().min(0)),
  CSFLOAT_FEE_PCT: z
    .string()
    .default('2.0')
    .transform((v) => Number(v))
    .pipe(z.number().min(0).max(50)),
  WHITELIST_ITEMS: z.string().optional(),
  BLACKLIST_ITEMS: z.string().optional(),
});

const parsed = EnvSchema.safeParse(process.env);
// Note: avoid console usage to satisfy lint; rely on consumers to handle env.

export type AppConfig = {
  csfloatApiKey?: string;
  csfloatSessionCookie?: string;
  csfloatCookiesHeader?: string;
  steamApiKey?: string;
  priceSource: 'steam' | 'csgobackpack';
  minRoiPct: number;
  maxInventoryUsd: number;
  csfloatFeePct: number;
  whitelistItems: string[];
  blacklistItems: string[];
};

export const loadConfig = (): AppConfig => {
  const env = parsed.success ? parsed.data : ({} as any);
  return {
    csfloatApiKey: env.CSFLOAT_API_KEY,
    csfloatSessionCookie: env.CSFLOAT_SESSION_COOKIE,
    csfloatCookiesHeader: env.CSFLOAT_COOKIES,
    steamApiKey: env.STEAM_API_KEY,
    priceSource: env.PRICE_SOURCE ?? 'steam',
    minRoiPct: env.MIN_ROI_PCT ?? 5,
    maxInventoryUsd: env.MAX_INVENTORY_USD ?? 200,
    csfloatFeePct: env.CSFLOAT_FEE_PCT ?? 2.0,
    whitelistItems: (env.WHITELIST_ITEMS ?? '')
      .split(',')
      .map((s: string) => s.trim())
      .filter(Boolean),
    blacklistItems: (env.BLACKLIST_ITEMS ?? '')
      .split(',')
      .map((s: string) => s.trim())
      .filter(Boolean),
  };
};


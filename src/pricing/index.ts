import { getSteamPriceCents } from './steam.js';
import { getCsgobackpackPriceCents } from './csgobackpack.js';

export async function getReferencePriceCents(
  marketHashName: string,
  source: 'steam' | 'csgobackpack',
): Promise<{ priceCents: number | null; sourceUsed: string }> {
  if (source === 'steam') {
    const p = await getSteamPriceCents(marketHashName);
    return { priceCents: p, sourceUsed: 'steam' };
  }
  const p = await getCsgobackpackPriceCents(marketHashName);
  return { priceCents: p, sourceUsed: 'csgobackpack' };
}


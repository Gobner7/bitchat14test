export type MarketListing = {
  listingId: string;
  marketHashName: string;
  priceCents: number;
  floatValue: number | null;
  assetId?: string;
  stickers?: string[];
  url: string;
  createdAt?: string;
};

export type PurchaseResult = {
  success: boolean;
  message?: string;
  orderId?: string;
};


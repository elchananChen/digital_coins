import os from "os";
import { EKrakenSymbol, EUsdSymbol } from "../types/orderBookTypes";
export function getLocalIP(): string | null {
  const interfaces = os.networkInterfaces();
  for (const name in interfaces) {
    for (const iface of interfaces[name]!) {
      if (iface.family === "IPv4" && !iface.internal) {
        return iface.address;
      }
    }
  }
  return null;
}

export function KrakenSymbolsToUsdSymbols(symbol: EKrakenSymbol): EUsdSymbol {
  const key = Object.keys(EKrakenSymbol).find(
    (k) => EKrakenSymbol[k as keyof typeof EKrakenSymbol] === symbol
  );

  if (!key || !(key in EUsdSymbol)) {
    throw new Error(
      `No matching USD symbol found for Kraken symbol: ${symbol}`
    );
  }

  return EUsdSymbol[key as keyof typeof EUsdSymbol];
}

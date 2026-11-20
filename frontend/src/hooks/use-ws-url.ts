import { useSyncExternalStore } from "react";
import { getWsBaseUrl } from "@/lib/api";

const subscribe = () => () => {};

/** The WebSocket URL on the client; an empty string during SSR (hydration-safe). */
export function useWsUrl(): string {
  return useSyncExternalStore(subscribe, getWsBaseUrl, () => "");
}

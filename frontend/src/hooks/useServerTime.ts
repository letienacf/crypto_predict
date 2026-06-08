import { useEffect, useMemo, useState } from "react";

interface UseServerTimeResult {
  nowMs: number;
  offsetMs: number;
}

async function fetchServerOffset(baseUrl: string): Promise<number> {
  const response = await fetch(`${baseUrl}/api/v1/system/time`);
  if (!response.ok) {
    throw new Error(`Failed to fetch server time, status=${response.status}`);
  }

  const payload = (await response.json()) as { server_time?: string };
  const rawServerTime = payload.server_time;
  if (typeof rawServerTime !== "string") {
    throw new Error("Missing server_time in response");
  }

  const serverMs = new Date(rawServerTime).getTime();
  return serverMs - Date.now();
}

export function useServerTime(baseUrl = ""): UseServerTimeResult {
  const [offsetMs, setOffsetMs] = useState<number>(0);
  const [tick, setTick] = useState<number>(Date.now());

  useEffect(() => {
    let disposed = false;

    const sync = async (): Promise<void> => {
      try {
        const nextOffset = await fetchServerOffset(baseUrl);
        if (!disposed) {
          setOffsetMs(nextOffset);
        }
      } catch {
        if (!disposed) {
          setOffsetMs(0);
        }
      }
    };

    void sync();
    const syncTimer = window.setInterval(() => {
      void sync();
    }, 30000);

    return () => {
      disposed = true;
      window.clearInterval(syncTimer);
    };
  }, [baseUrl]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setTick(Date.now());
    }, 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, []);

  const nowMs = useMemo(() => tick + offsetMs, [tick, offsetMs]);
  return { nowMs, offsetMs };
}

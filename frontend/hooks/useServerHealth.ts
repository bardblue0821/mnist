import { useState, useEffect } from "react";
import { toast } from "sonner";

const POLL_INTERVAL_MS = 3000;
const MAX_ATTEMPTS = 20; // 3s × 20 = 60s

interface UseServerHealthReturn {
  isServerReady: boolean;
}

export function useServerHealth(): UseServerHealthReturn {
  const [isServerReady, setIsServerReady] = useState(false);

  useEffect(() => {
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout>;

    const check = async () => {
      try {
        const res = await fetch("/api/health", {
          signal: AbortSignal.timeout(5000),
        });
        if (res.ok) {
          setIsServerReady(true);
          return;
        }
      } catch {
        /* ignore */
      }

      attempts++;
      if (attempts >= MAX_ATTEMPTS) {
        toast.error(
          "サーバーに接続できません。しばらくしてからアクセスしてください。"
        );
        return;
      }
      timer = setTimeout(check, POLL_INTERVAL_MS);
    };

    check();
    return () => clearTimeout(timer);
  }, []);

  return { isServerReady };
}

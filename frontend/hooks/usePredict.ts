import { useState, useCallback, useRef, useEffect } from "react";
import { toast } from "sonner";
import type { Prediction, PredictResponse } from "@/types/prediction";

const INITIAL_PREDICTIONS: Prediction[] = Array.from({ length: 10 }, (_, i) => ({
  digit: i,
  probability: 0,
}));

const DEBOUNCE_MS = 500;

interface UsePredictReturn {
  predictions: Prediction[];
  predict: (imageBase64: string) => void;
  resetPredictions: () => void;
  isLoading: boolean;
}

export function usePredict(): UsePredictReturn {
  const [predictions, setPredictions] = useState<Prediction[]>(INITIAL_PREDICTIONS);
  const [isLoading, setIsLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const predict = useCallback((imageBase64: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const res = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imageBase64 }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "予測に失敗しました");
        }
        const data: PredictResponse = await res.json();
        setPredictions(data.predictions);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "エラーが発生しました");
      } finally {
        setIsLoading(false);
      }
    }, DEBOUNCE_MS);
  }, []);

  const resetPredictions = useCallback(() => {
    setPredictions(INITIAL_PREDICTIONS);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { predictions, predict, resetPredictions, isLoading };
}

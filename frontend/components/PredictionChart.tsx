import type { Prediction } from "@/types/prediction";

interface PredictionChartProps {
  predictions: Prediction[];
}

export function PredictionChart({ predictions }: PredictionChartProps) {
  const maxProb = Math.max(...predictions.map((p) => p.probability));

  return (
    <div className="w-full max-w-md">
      {predictions.map(({ digit, probability }) => {
        const percentage = (probability * 100).toFixed(1);
        const isMax = probability === maxProb && maxProb > 0;
        return (
          <div key={digit} className="flex items-center gap-2 mb-1">
            <span className="w-6 text-right font-mono text-lg">{digit}</span>
            <div className="flex-1 bg-gray-800 rounded h-6 overflow-hidden">
              <div
                data-testid={`bar-${digit}`}
                className={`h-full rounded transition-all duration-300 ease-out ${
                  isMax ? "bg-blue-500" : "bg-gray-500"
                }`}
                style={{ width: `${probability * 100}%` }}
              />
            </div>
            <span className="w-16 text-right text-sm font-mono">
              {percentage}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

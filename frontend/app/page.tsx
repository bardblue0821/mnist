"use client";

import { Canvas } from "@/components/Canvas";
import { PredictionChart } from "@/components/PredictionChart";
import { WarmupOverlay } from "@/components/WarmupOverlay";
import { usePredict } from "@/hooks/usePredict";
import { useServerHealth } from "@/hooks/useServerHealth";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  const { isServerReady } = useServerHealth();
  const { predictions, predict, resetPredictions } = usePredict();

  const handleDraw = (imageBase64: string) => {
    predict(imageBase64);
  };

  const handleClear = () => {
    resetPredictions();
  };

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 p-6 bg-white text-zinc-900">
      {!isServerReady && <WarmupOverlay />}
      <h1 className="text-3xl font-bold text-teal-600">手書き数字認識</h1>
      <div className="flex flex-col md:flex-row gap-8 items-start">
        <Card className="bg-white border-teal-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-zinc-800">キャンバス</CardTitle>
          </CardHeader>
          <CardContent>
            <Canvas onDraw={handleDraw} onClear={handleClear} />
          </CardContent>
        </Card>
        <Card className="bg-white border-teal-200 shadow-sm min-w-[320px]">
          <CardHeader>
            <CardTitle className="text-zinc-800">予測結果</CardTitle>
          </CardHeader>
          <CardContent>
            <PredictionChart predictions={predictions} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

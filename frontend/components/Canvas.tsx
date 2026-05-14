"use client";

import { Eraser } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCanvas } from "@/hooks/useCanvas";

interface CanvasProps {
  onDraw: (imageBase64: string) => void;
  onClear: () => void;
}

export function Canvas({ onDraw, onClear }: CanvasProps) {
  const { canvasRef, handlePointerDown, handlePointerMove, handlePointerUp, clear } =
    useCanvas(onDraw);

  const handleClear = () => {
    clear();
    onClear();
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={280}
        height={280}
        className="border border-teal-700 rounded-lg cursor-crosshair w-full max-w-[280px] aspect-square touch-none"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      />
      <Button onClick={handleClear} variant="outline" className="mt-4">
        <Eraser className="mr-2 h-4 w-4" />
        クリア
      </Button>
    </div>
  );
}

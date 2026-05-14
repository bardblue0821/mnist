import { useRef, useEffect, useCallback } from "react";

const CANVAS_SIZE = 280;
const PEN_WIDTH = 15;
const PEN_COLOR = "#FFFFFF";
const BG_COLOR = "#000000";

interface UseCanvasReturn {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  handlePointerDown: (e: React.PointerEvent) => void;
  handlePointerMove: (e: React.PointerEvent) => void;
  handlePointerUp: () => void;
  clear: () => void;
}

export function useCanvas(
  onDraw: (imageBase64: string) => void
): UseCanvasReturn {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDrawing = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  }, []);

  const getCoords = useCallback(
    (e: React.PointerEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return { x: 0, y: 0 };
      const rect = canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left) * (CANVAS_SIZE / rect.width),
        y: (e.clientY - rect.top) * (CANVAS_SIZE / rect.height),
      };
    },
    []
  );

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      isDrawing.current = true;
      const ctx = canvasRef.current?.getContext("2d");
      if (!ctx) return;
      const { x, y } = getCoords(e);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.strokeStyle = PEN_COLOR;
      ctx.lineWidth = PEN_WIDTH;
    },
    [getCoords]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDrawing.current) return;
      const ctx = canvasRef.current?.getContext("2d");
      if (!ctx) return;
      const { x, y } = getCoords(e);
      ctx.lineTo(x, y);
      ctx.stroke();
      const dataUrl = canvasRef.current!.toDataURL("image/png");
      onDraw(dataUrl);
    },
    [getCoords, onDraw]
  );

  const handlePointerUp = useCallback(() => {
    isDrawing.current = false;
  }, []);

  const clear = useCallback(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
  }, []);

  return { canvasRef, handlePointerDown, handlePointerMove, handlePointerUp, clear };
}

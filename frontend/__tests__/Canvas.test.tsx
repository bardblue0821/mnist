import { render, screen, fireEvent } from "@testing-library/react";
import { Canvas } from "@/components/Canvas";

// jsdom には Canvas API がないため mock
const mockContext = {
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  stroke: jest.fn(),
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  set fillStyle(_v: string) {},
  set strokeStyle(_v: string) {},
  set lineWidth(_v: number) {},
  set lineCap(_v: string) {},
  set lineJoin(_v: string) {},
};

HTMLCanvasElement.prototype.getContext = jest.fn(() => mockContext) as any;
HTMLCanvasElement.prototype.toDataURL = jest.fn(() => "data:image/png;base64,AAAA");

describe("Canvas", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("キャンバスが描画される", () => {
    render(<Canvas onDraw={jest.fn()} onClear={jest.fn()} />);
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  test("PointerDown + PointerMove で onDraw が呼ばれる", () => {
    const onDraw = jest.fn();
    render(<Canvas onDraw={onDraw} onClear={jest.fn()} />);
    const canvas = document.querySelector("canvas")!;

    fireEvent.pointerDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.pointerMove(canvas, { clientX: 110, clientY: 110 });

    expect(onDraw).toHaveBeenCalledWith("data:image/png;base64,AAAA");
  });

  test("クリアボタンで描画がリセットされる", () => {
    const onClear = jest.fn();
    render(<Canvas onDraw={jest.fn()} onClear={onClear} />);
    const clearButton = screen.getByRole("button", { name: /クリア/ });

    fireEvent.click(clearButton);

    expect(mockContext.fillRect).toHaveBeenCalled();
    expect(onClear).toHaveBeenCalled();
  });

  test("touch-none が設定されている", () => {
    render(<Canvas onDraw={jest.fn()} onClear={jest.fn()} />);
    const canvas = document.querySelector("canvas")!;
    expect(canvas.className).toContain("touch-none");
  });
});

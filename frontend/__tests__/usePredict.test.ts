import { renderHook, act } from "@testing-library/react";
import { usePredict } from "@/hooks/usePredict";

// sonner の toast を mock
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

import { toast } from "sonner";

const mockPredictions = Array.from({ length: 10 }, (_, i) => ({
  digit: i,
  probability: i === 7 ? 0.95 : 0.005556,
}));

describe("usePredict", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("predict() で API が呼ばれる", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ predictions: mockPredictions }),
    });

    const { result } = renderHook(() => usePredict());

    act(() => {
      result.current.predict("data:image/png;base64,AAAA");
    });

    // 500ms デバウンス待ち
    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: "data:image/png;base64,AAAA" }),
    });
  });

  test("500ms デバウンスが機能する", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ predictions: mockPredictions }),
    });

    const { result } = renderHook(() => usePredict());

    act(() => {
      result.current.predict("data:image/png;base64,AAA1");
      result.current.predict("data:image/png;base64,AAA2");
      result.current.predict("data:image/png;base64,AAA3");
    });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    // 最後の1回のみ fetch される
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/predict",
      expect.objectContaining({
        body: JSON.stringify({ image: "data:image/png;base64,AAA3" }),
      })
    );
  });

  test("API エラー時にトーストが表示される", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: "Invalid image" }),
    });

    const { result } = renderHook(() => usePredict());

    act(() => {
      result.current.predict("data:image/png;base64,BAD");
    });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(toast.error).toHaveBeenCalledWith("Invalid image");
  });

  test("resetPredictions() で初期値に戻る", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ predictions: mockPredictions }),
    });

    const { result } = renderHook(() => usePredict());

    act(() => {
      result.current.predict("data:image/png;base64,AAAA");
    });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    // predictions が更新されたことを確認
    expect(result.current.predictions[7].probability).toBe(0.95);

    act(() => {
      result.current.resetPredictions();
    });

    // 全て 0 に戻る
    result.current.predictions.forEach((p) => {
      expect(p.probability).toBe(0);
    });
  });
});

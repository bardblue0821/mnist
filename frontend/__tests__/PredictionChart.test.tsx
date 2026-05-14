import { render, screen } from "@testing-library/react";
import { PredictionChart } from "@/components/PredictionChart";
import type { Prediction } from "@/types/prediction";

const zeroPredictions: Prediction[] = Array.from({ length: 10 }, (_, i) => ({
  digit: i,
  probability: 0,
}));

const samplePredictions: Prediction[] = Array.from({ length: 10 }, (_, i) => ({
  digit: i,
  probability: i === 3 ? 0.82 : 0.02,
}));

describe("PredictionChart", () => {
  test("全10桁が表示される", () => {
    render(<PredictionChart predictions={zeroPredictions} />);
    for (let i = 0; i <= 9; i++) {
      expect(screen.getByText(String(i))).toBeInTheDocument();
    }
  });

  test("正規化後の最大確率が100%で表示される", () => {
    render(<PredictionChart predictions={samplePredictions} />);
    expect(screen.getByText("100.0%")).toBeInTheDocument();
  });

  test("最大確率の数字がtealでハイライトされる", () => {
    const { container } = render(
      <PredictionChart predictions={samplePredictions} />
    );
    const bars = container.querySelectorAll("[data-testid^='bar-']");
    const bar3 = container.querySelector("[data-testid='bar-3']");
    expect(bar3).toHaveClass("bg-teal-400");
    // 他のバーは bg-zinc-500
    bars.forEach((bar) => {
      if (bar.getAttribute("data-testid") !== "bar-3") {
        expect(bar).toHaveClass("bg-zinc-500");
      }
    });
  });

  test("初期状態で全て 0%", () => {
    const { container } = render(
      <PredictionChart predictions={zeroPredictions} />
    );
    const bars = container.querySelectorAll("[data-testid^='bar-']");
    bars.forEach((bar) => {
      expect(bar).toHaveStyle({ width: "0%" });
    });
  });

  test("正規化で最大が100%、最小が0%になる", () => {
    const { container } = render(
      <PredictionChart predictions={samplePredictions} />
    );
    const bar3 = container.querySelector("[data-testid='bar-3']");
    expect(bar3).toHaveStyle({ width: "100%" });

    // 最小確率のバーは 0%
    const bar0 = container.querySelector("[data-testid='bar-0']");
    expect(bar0).toHaveStyle({ width: "0%" });
  });
});

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

  test("確率が%で表示される", () => {
    render(<PredictionChart predictions={samplePredictions} />);
    expect(screen.getByText("82.0%")).toBeInTheDocument();
  });

  test("最大確率の数字がハイライトされる", () => {
    const { container } = render(
      <PredictionChart predictions={samplePredictions} />
    );
    const bars = container.querySelectorAll("[data-testid^='bar-']");
    const bar3 = container.querySelector("[data-testid='bar-3']");
    expect(bar3).toHaveClass("bg-blue-500");
    // 他のバーは bg-gray-500
    bars.forEach((bar) => {
      if (bar.getAttribute("data-testid") !== "bar-3") {
        expect(bar).toHaveClass("bg-gray-500");
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
});

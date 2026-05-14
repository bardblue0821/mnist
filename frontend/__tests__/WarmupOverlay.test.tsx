import { render, screen } from "@testing-library/react";
import { WarmupOverlay } from "@/components/WarmupOverlay";

describe("WarmupOverlay", () => {
  test("オーバーレイが表示される", () => {
    render(<WarmupOverlay />);
    expect(screen.getByText("サーバー起動中...")).toBeInTheDocument();
    expect(
      screen.getByText("初回アクセス時は30秒ほどかかる場合があります")
    ).toBeInTheDocument();
  });
});

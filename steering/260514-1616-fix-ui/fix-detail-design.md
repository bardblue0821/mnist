# UI修正 詳細設計書

## 修正元: fix.md

---

## 修正1: 予測結果の正規化

### 背景

バックエンドの softmax 出力はそのまま表示されるが、分布が平坦なとき（例: 最大 23.2%、他 8.5%）、ユーザーに「本当に認識できてるの？」という不信感を与える。

### 方針

フロントエンド側で **Min-Max 正規化** を適用し、表示上の確率を 0%〜100% に引き伸ばす。

$$
\text{normalized}_i = \frac{p_i - p_{\min}}{p_{\max} - p_{\min}}
$$

- $p_{\max} = p_{\min}$（全て同値）の場合は全て 0% とする
- API からの生の確率はそのままに、**表示専用の正規化値**を計算する

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `components/PredictionChart.tsx` | Min-Max 正規化ロジック追加、バー幅と%表示を正規化値で描画 |
| `__tests__/PredictionChart.test.tsx` | 正規化後の値でテスト修正・追加 |

### PredictionChart.tsx 変更詳細

```tsx
export function PredictionChart({ predictions }: PredictionChartProps) {
  const probs = predictions.map((p) => p.probability);
  const minProb = Math.min(...probs);
  const maxProb = Math.max(...probs);
  const range = maxProb - minProb;

  // 正規化関数: 0〜1 にスケーリング
  const normalize = (prob: number): number => {
    if (range === 0) return 0;
    return (prob - minProb) / range;
  };

  return (
    <div className="w-full max-w-md">
      {predictions.map(({ digit, probability }) => {
        const normalized = normalize(probability);
        const percentage = (normalized * 100).toFixed(1);
        const isMax = probability === maxProb && maxProb > 0;
        return (
          <div key={digit} className="flex items-center gap-2 mb-1">
            <span className="w-6 text-right font-mono text-lg">{digit}</span>
            <div className="flex-1 bg-gray-800 rounded h-6 overflow-hidden">
              <div
                data-testid={`bar-${digit}`}
                className={`h-full rounded transition-all duration-300 ease-out ${
                  isMax ? "bg-teal-400" : "bg-zinc-500"
                }`}
                style={{ width: `${normalized * 100}%` }}
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
```

### テスト変更詳細

| # | テストケース | 変更内容 |
|---|---|---|
| 1 | 全10桁が表示される | 変更なし |
| 2 | 確率が%で表示される | 正規化後の最大値 → `"100.0%"` に変更 |
| 3 | 最大確率がハイライト | `bg-blue-500` → `bg-teal-400` に変更 |
| 4 | 初期状態で全て 0% | 変更なし（全同値 → 全0%のまま） |
| 5 | **新規**: 正規化で最大が100%、最小が0% | 追加 |

---

## 修正2: アクセシビリティ（teal 系カラー）

### 背景

現在の配色（bg-zinc-950 背景 + bg-gray-500/bg-blue-500 バー + text-white）はコントラストが微妙で視認性が低い。

### 方針

teal 系のアクセントカラーを導入し、以下を改善する:

- プライマリバー色: `bg-blue-500` → **`bg-teal-400`**（WCAG AA 基準の黒背景とのコントラスト比 OK）
- 非アクティブバー色: `bg-gray-500` → **`bg-zinc-500`**
- Card ボーダー: `border-zinc-700` → **`border-teal-900`**
- h1 タイトル: `text-white` → **`text-teal-300`**
- キャンバス枠線: `border-gray-600` → **`border-teal-700`**
- クリアボタン: outline variant のまま、hover 時に teal アクセントが出る形にする
- WarmupOverlay スピナー: `text-white` → **`text-teal-400`**

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `components/PredictionChart.tsx` | バーの色を teal 系に変更（修正1と統合済み） |
| `components/Canvas.tsx` | キャンバス border 色変更 |
| `components/WarmupOverlay.tsx` | スピナー色を teal に |
| `app/page.tsx` | h1・Card のアクセントカラー変更 |
| `__tests__/PredictionChart.test.tsx` | `bg-blue-500` → `bg-teal-400` に変更 |
| `__tests__/Canvas.test.tsx` | 必要に応じて className 検証を調整 |
| `__tests__/WarmupOverlay.test.tsx` | 変更なし（テキスト内容は不変） |

### 各ファイルの変更マッピング

#### `app/page.tsx`

```diff
- <main className="... bg-zinc-950 text-white">
+ <main className="... bg-zinc-950 text-zinc-100">

- <h1 className="text-3xl font-bold">
+ <h1 className="text-3xl font-bold text-teal-300">

- <Card className="bg-zinc-900 border-zinc-700">
+ <Card className="bg-zinc-900 border-teal-900">
  (両方の Card に適用)
```

#### `components/Canvas.tsx`

```diff
- className="border border-gray-600 rounded-lg ..."
+ className="border border-teal-700 rounded-lg ..."
```

#### `components/WarmupOverlay.tsx`

```diff
- <Loader2 className="h-8 w-8 animate-spin" />
+ <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
```

---

## 実装順序

| # | ステップ | 説明 |
|---|---|---|
| 1 | `PredictionChart.tsx` 修正 | Min-Max 正規化 + teal カラー |
| 2 | `PredictionChart.test.tsx` 修正 | テスト修正・追加 |
| 3 | テスト実行 → GREEN 確認 | `npx jest __tests__/PredictionChart.test.tsx` |
| 4 | `Canvas.tsx` 修正 | border 色変更 |
| 5 | `WarmupOverlay.tsx` 修正 | スピナー色変更 |
| 6 | `page.tsx` 修正 | h1・Card アクセントカラー |
| 7 | 全テスト実行 → GREEN 確認 | `npx jest` |
| 8 | ブラウザで目視確認 | `npm run dev` |

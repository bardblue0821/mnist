# 基本設計書

## 1. システム構成図

```
┌─────────────────────────────────────────────────┐
│                Render (Docker)                  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │            FastAPI (Python)                │  │
│  │                                           │  │
│  │  /api/predict  ─→ 前処理 ─→ TFLite推論   │  │
│  │  /api/health   ─→ ヘルスチェック          │  │
│  │  /*            ─→ 静的ファイル配信        │  │
│  │                   (Next.js ビルド成果物)   │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ model.tflite │  │  out/ (静的HTML/JS/CSS) │  │
│  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────┘
        ▲
        │ HTTPS
        ▼
┌──────────────┐
│   ブラウザ    │
│  (React SPA) │
└──────────────┘
```

## 2. ディレクトリ構成

```
mnist/
├── README.md
├── doc/
│   ├── requirement.md          # 要求仕様書
│   ├── design.md               # 基本設計書（本書）
│   ├── detail-design.md        # 詳細設計書
│   └── policy.md               # 実装ポリシー
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── jest.config.ts
│   ├── postcss.config.mjs
│   ├── app/
│   │   ├── layout.tsx          # ルートレイアウト
│   │   └── page.tsx            # メインページ
│   ├── components/
│   │   ├── Canvas.tsx          # 描画キャンバス
│   │   ├── PredictionChart.tsx # 棒グラフ表示
│   │   └── WarmupOverlay.tsx   # コールドスタート表示
│   ├── components/ui/          # shadcn/ui コンポーネント
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── progress.tsx
│   │   ├── skeleton.tsx
│   │   └── sonner.tsx
│   ├── hooks/
│   │   ├── useCanvas.ts        # キャンバス描画ロジック
│   │   └── usePredict.ts       # API呼び出し＋デバウンス
│   └── __tests__/
│       ├── Canvas.test.tsx
│       ├── PredictionChart.test.tsx
│       ├── WarmupOverlay.test.tsx
│       ├── useCanvas.test.ts
│       └── usePredict.test.ts
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI アプリケーション
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── predict.py      # /api/predict エンドポイント
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── preprocessor.py # 画像前処理
│   │   │   └── predictor.py    # TFLite推論
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── predict.py      # リクエスト/レスポンスモデル
│   │   └── models/
│   │       └── model.tflite    # 学習済みモデル
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_predict_api.py
│       ├── test_preprocessor.py
│       └── test_predictor.py
└── ml/
    ├── requirements.txt
    ├── train.py                # モデルトレーニングスクリプト
    ├── evaluate.py             # 精度評価スクリプト
    └── export_tflite.py        # TFLite変換スクリプト
```

## 3. フロントエンド設計

### 3.1 画面レイアウト

```
┌────────────────────────────────────────┐
│         手書き数字認識                  │
│                                        │
│  ┌──────────────┐  ┌────────────────┐  │
│  │              │  │ 0 ██░░░░  5%   │  │
│  │              │  │ 1 ░░░░░░  1%   │  │
│  │   キャンバス  │  │ 2 ░░░░░░  2%   │  │
│  │  (280x280)   │  │ 3 ░░░░░░  1%   │  │
│  │   黒背景     │  │ 4 ░░░░░░  3%   │  │
│  │   白ペン     │  │ 5 ░░░░░░  1%   │  │
│  │              │  │ 6 ░░░░░░  2%   │  │
│  │              │  │ 7 ████████ 82% │  │
│  │              │  │ 8 ░░░░░░  2%   │  │
│  └──────────────┘  │ 9 ░░░░░░  1%   │  │
│                    └────────────────┘  │
│        [クリア]                        │
│                                        │
└────────────────────────────────────────┘
```

- PC: キャンバスと棒グラフを横並び（flex row）
- スマートフォン: 縦並び（flex col）に切り替え（Tailwind `md:` ブレークポイント）

### 3.2 コンポーネント設計

#### `app/page.tsx` — メインページ
- 状態管理:
  - `predictions: {digit: number, probability: number}[]` — 推論結果（初期値: 全て 0%）
  - `isServerReady: boolean` — サーバー起動状態
- マウント時に `/api/health` をポーリング（3秒間隔、最大60秒）してサーバー起動を待つ
- `Canvas` と `PredictionChart` を配置

#### `components/Canvas.tsx` — 描画キャンバス
- Props: `onDraw: (imageData: string) => void`
- HTML5 Canvas 要素を使用
- `useCanvas` フックで描画ロジックを管理
- 描画イベント: `pointerdown/pointermove/pointerup`
- shadcn/ui `Button` で「クリア」ボタンを実装
- shadcn/ui `Card` でキャンバスをラップ

#### `components/PredictionChart.tsx` — 棒グラフ
- Props: `predictions: {digit: number, probability: number}[]`
- 0〜9 の水平バーを shadcn/ui `Progress` または Tailwind CSS で描画
- バー幅: `probability * 100%`、CSS `transition: width 300ms ease`
- 最大確率の数字は背景色を変える（ハイライト）

#### `components/WarmupOverlay.tsx` — コールドスタート表示
- Props: `isReady: boolean`
- `isReady === false` の間、画面全体にオーバーレイ + shadcn/ui `Skeleton` + スピナー +「サーバー起動中...」を表示

### 3.3 カスタムフック設計

#### `hooks/useCanvas.ts`
- `canvasRef: RefObject<HTMLCanvasElement>`
- `isDrawing: boolean` — 描画中フラグ
- `startDraw()` / `draw()` / `endDraw()` — 描画イベントハンドラ
- `clear()` — キャンバスクリア
- `getImageAsBase64(): string` — キャンバスを PNG Base64 に変換

#### `hooks/usePredict.ts`
- `predictions` state を管理
- `predict(imageBase64: string)` — `/api/predict` を呼び出し結果を更新
- **デバウンス処理**: `onDraw` コールバックが呼ばれるたびに 500ms タイマーをリセット。500ms 経過後に `predict()` を実行
- エラー時は `sonner`（shadcn/ui 推奨トースト）でトースト通知

### 3.4 データフロー

```
Canvas描画
  → endDraw / draw停止
  → デバウンス 500ms
  → canvas.toDataURL("image/png")
  → Base64文字列を取得
  → POST /api/predict { image: "data:image/png;base64,..." }
  → レスポンス { predictions: [...] }
  → PredictionChart に反映（CSSトランジションで滑らかに更新）
```

## 4. バックエンド設計

### 4.1 FastAPI アプリケーション構成

#### `app/main.py`
- FastAPI インスタンス生成
- `lifespan` イベントでモデルを起動時にロード（`app.state.predictor`）
- `/api` ルーターをマウント
- Next.js 静的ファイルを `StaticFiles` でマウント（`/` にフォールバック）

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: モデルロード
    app.state.predictor = Predictor("app/models/model.tflite")
    yield
    # 終了時: クリーンアップ

app = FastAPI(lifespan=lifespan)
app.include_router(predict_router, prefix="/api")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

#### `app/routers/predict.py`
- `POST /api/predict` — 推論エンドポイント
- `GET /api/health` — ヘルスチェック

```python
@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, app=Depends(get_app)):
    image = preprocessor.preprocess(request.image)
    predictions = app.state.predictor.predict(image)
    return PredictResponse(predictions=predictions)

@router.get("/health")
async def health():
    return {"status": "ok"}
```

### 4.2 スキーマ定義

#### `app/schemas/predict.py`

```python
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    image: str = Field(..., description="Base64エンコードされたPNG画像")

class Prediction(BaseModel):
    digit: int = Field(..., ge=0, le=9)
    probability: float = Field(..., ge=0.0, le=1.0)

class PredictResponse(BaseModel):
    predictions: list[Prediction]
```

### 4.3 画像前処理

#### `app/services/preprocessor.py`

```
入力: Base64 PNG文字列（"data:image/png;base64,..." または生Base64）
  ↓
1. Base64デコード → バイト列
2. PIL.Image.open() → RGBAイメージ
3. グレースケール変換 (.convert("L"))
4. 28×28px にリサイズ (Image.LANCZOS)
5. NumPy配列に変換
6. 正規化: pixel / 255.0
7. 形状変換: (1, 28, 28, 1) — バッチ次元+チャネル次元
  ↓
出力: np.ndarray (1, 28, 28, 1) float32
```

バリデーション:
- Base64 デコード失敗 → HTTP 400
- 画像サイズ上限: 1MB → HTTP 400
- 画像デコード失敗 → HTTP 400

### 4.4 TFLite 推論

#### `app/services/predictor.py`

```python
import numpy as np
from tflite_runtime.interpreter import Interpreter

class Predictor:
    def __init__(self, model_path: str):
        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def predict(self, image: np.ndarray) -> list[dict]:
        self.interpreter.set_tensor(self.input_details[0]["index"], image)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]["index"])
        probabilities = softmax(output[0])
        return [
            {"digit": i, "probability": float(p)}
            for i, p in enumerate(probabilities)
        ]
```

### 4.5 ログ設計

- Python 標準 `logging` モジュールを使用
- ログレベル: `INFO`（本番）、`DEBUG`（開発）
- 出力先: 標準出力（Render のログ機能で閲覧）
- ログ内容:
  - リクエスト受信（パスのみ、画像データはログしない）
  - 推論結果（トップ3の数字と確率）
  - エラー発生時のスタックトレース

## 5. 機械学習モデル設計

### 5.1 CNN アーキテクチャ

```
入力: (28, 28, 1)
  ↓
Conv2D(32, 3×3, ReLU) → MaxPool2D(2×2)
  ↓
Conv2D(64, 3×3, ReLU) → MaxPool2D(2×2)
  ↓
Flatten
  ↓
Dense(128, ReLU) → Dropout(0.5)
  ↓
Dense(10, Softmax)
  ↓
出力: (10,) — 0〜9の確率
```

### 5.2 トレーニング設定

| 項目 | 値 |
|---|---|
| データセット | MNIST (60,000 train / 10,000 test) |
| オプティマイザ | Adam |
| 学習率 | 0.001 |
| 損失関数 | Categorical Crossentropy |
| バッチサイズ | 128 |
| エポック数 | 10（Early Stopping 付き） |
| データ拡張 | 回転（±10°）、シフト（±10%） |

### 5.3 ワークフロー

```
ml/train.py
  → Keras でモデル定義・トレーニング
  → model.keras として保存

ml/evaluate.py
  → テストデータで精度評価
  → 95% 未満の場合はエラー終了

ml/export_tflite.py
  → model.keras → model.tflite に変換
  → backend/app/models/model.tflite にコピー
```

## 6. デプロイメント設計

### 6.1 ローカル開発

ローカル開発時はフロントエンドとバックエンドを個別に起動する:

```
# ターミナル 1: バックエンド
cd backend
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# ターミナル 2: フロントエンド
cd frontend
npm install
npm run dev
```

- フロントエンド: `http://localhost:3000`（Next.js dev server）
- バックエンド: `http://localhost:8000`（FastAPI + uvicorn --reload）
- フロントエンドから `/api/*` へのリクエストは `next.config.ts` の `rewrites` でバックエンドにプロキシ

### 6.2 Render デプロイ

- Render にデプロイする際は Dockerfile を使用する（ローカルでは Docker 不使用）。

| 項目 | 値 |
|---|---|
| サービスタイプ | Web Service |
| 環境 | Docker |
| プラン | Free |
| ヘルスチェックパス | `/api/health` |
| 自動デプロイ | main ブランチ push 時 |

## 7. テスト設計

### 7.1 フロントエンド（Jest + React Testing Library）

| テスト対象 | テスト内容 |
|---|---|
| `Canvas` | キャンバス描画イベント発火、クリア動作 |
| `PredictionChart` | 確率データの表示、ハイライト表示 |
| `WarmupOverlay` | `isReady=false` でオーバーレイ表示、`true` で非表示 |
| `useCanvas` | `getImageAsBase64()` が Base64 文字列を返す |
| `usePredict` | API 呼び出し、デバウンス動作、エラー時トースト表示 |

### 7.2 バックエンド（pytest）

| テスト対象 | テスト内容 |
|---|---|
| `POST /api/predict` | 正常系: 有効な画像 → 10要素の確率配列が返る |
| `POST /api/predict` | 異常系: 不正な Base64 → 400 エラー |
| `POST /api/predict` | 異常系: サイズ超過 → 400 エラー |
| `GET /api/health` | `{"status": "ok"}` が返る |
| `preprocessor` | 280×280 PNG → (1,28,28,1) float32 配列に変換される |
| `preprocessor` | 不正データ → 例外送出 |
| `predictor` | (1,28,28,1) 入力 → 10要素の確率配列（合計≒1.0） |

### 7.3 モデル（evaluate.py）

| テスト内容 | 合格基準 |
|---|---|
| MNIST テストデータ（10,000枚）での正解率 | ≧ 95% |
| 推論時間（1枚あたり） | < 50ms |

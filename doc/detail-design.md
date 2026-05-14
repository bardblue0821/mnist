# 詳細設計書

## 1. 技術スタック・バージョン

| カテゴリ | 技術 | バージョン |
|---|---|---|
| フロントエンド | Next.js (App Router) | 15.x |
| フロントエンド | React | 19.x |
| フロントエンド | TypeScript | 5.x |
| フロントエンド | Tailwind CSS | 4.x |
| フロントエンド | shadcn/ui | 最新 |
| フロントエンド | sonner | 2.x |
| フロントエンド | lucide-react | 最新 |
| バックエンド | Python | 3.11 |
| バックエンド | FastAPI | 0.115.x |
| バックエンド | uvicorn | 0.34.x |
| バックエンド | Pillow | 11.x |
| バックエンド | NumPy | 1.x |
| バックエンド | tflite-runtime | 2.14.x |
| ML（トレーニング専用） | TensorFlow / Keras | 2.17.x |
| テスト | Jest | 29.x |
| テスト | React Testing Library | 16.x |
| テスト | pytest | 8.x |
| テスト | httpx | 0.28.x |
| インフラ | Node.js (ビルド用) | 20.x |

---

## 2. フロントエンド詳細設計

### 2.1 Next.js 設定

#### `next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",        // 静的エクスポート
  trailingSlash: true,
  images: {
    unoptimized: true,     // 静的エクスポートでは Image Optimization 無効
  },
  // ローカル開発時のみ: API リクエストをバックエンドにプロキシ
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

> **注意**: `output: "export"` 時は `rewrites` は無効になる。開発時（`npm run dev`）のみ有効。本番では FastAPI が静的ファイルと API を同一オリジンで配信するため不要。

#### `tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

### 2.2 型定義

#### `types/prediction.ts`

```typescript
/** 1つの数字の予測結果 */
export interface Prediction {
  digit: number;       // 0〜9
  probability: number; // 0.0〜1.0
}

/** /api/predict レスポンス */
export interface PredictResponse {
  predictions: Prediction[];
}

/** /api/predict エラーレスポンス */
export interface ErrorResponse {
  detail: string;
}

/** /api/health レスポンス */
export interface HealthResponse {
  status: string;
}
```

### 2.3 コンポーネント詳細

#### 2.3.1 `app/layout.tsx`

```typescript
// Props: children
// 責務:
//   - HTML の lang="ja" を設定
//   - Toaster コンポーネント（sonner）をマウント
//   - グローバル CSS（Tailwind）を読み込み
//   - メタデータ: title="手書き数字認識", description="..."
```

#### 2.3.2 `app/page.tsx`

```
状態:
  predictions: Prediction[]     — 初期値: [{digit:0, probability:0}, ..., {digit:9, probability:0}]
  isServerReady: boolean        — 初期値: false

マウント時:
  1. checkServerHealth() を呼び出し
     - GET /api/health を 3秒間隔でポーリング
     - 成功（status: "ok"）→ isServerReady = true、ポーリング停止
     - 60秒経過しても失敗 → トースト表示「サーバーに接続できません」
     - isServerReady = true のまま維持

描画コールバック:
  onDraw(imageBase64: string):
    - usePredict フックの predict() を呼び出し
    - predict() 内でデバウンス → API呼び出し → predictions 更新

レンダリング:
  <main>
    {!isServerReady && <WarmupOverlay />}
    <h1>手書き数字認識</h1>
    <div className="flex flex-col md:flex-row gap-8">
      <Card>
        <Canvas onDraw={handleDraw} />
      </Card>
      <Card>
        <PredictionChart predictions={predictions} />
      </Card>
    </div>
  </main>
```

#### 2.3.3 `components/Canvas.tsx`

```
Props:
  onDraw: (imageBase64: string) => void  — 描画変化時のコールバック

内部状態（useCanvas フック経由）:
  canvasRef: RefObject<HTMLCanvasElement>
  isDrawing: boolean

定数:
  CANVAS_SIZE = 280        — キャンバスの描画解像度（px）
  PEN_WIDTH = 15           — ペンの太さ（px）
  PEN_COLOR = "#FFFFFF"    — 白
  BG_COLOR = "#000000"     — 黒

初期化:
  - canvas の width/height を CANVAS_SIZE に設定
  - 2D コンテキスト取得
  - 黒で全面塗りつぶし
  - lineCap = "round", lineJoin = "round"

イベントハンドラ:
  handlePointerDown(e: PointerEvent):
    - isDrawing = true
    - ctx.beginPath()
    - ctx.moveTo(x, y)  ※座標変換あり（後述）

  handlePointerMove(e: PointerEvent):
    - if (!isDrawing) return
    - ctx.lineTo(x, y)
    - ctx.stroke()
    - onDraw(canvas.toDataURL("image/png"))

  handlePointerUp():
    - isDrawing = false

  座標変換:
    - canvas の CSS サイズと実際の描画サイズが異なる場合（レスポンシブ時）
    - x = (e.clientX - rect.left) * (CANVAS_SIZE / rect.width)
    - y = (e.clientY - rect.top) * (CANVAS_SIZE / rect.height)

  クリア:
    - ctx.fillStyle = BG_COLOR
    - ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
    - 親に predictions リセットを通知（onDraw は呼ばない）

レンダリング:
  <div>
    <canvas
      ref={canvasRef}
      width={CANVAS_SIZE}
      height={CANVAS_SIZE}
      className="border border-gray-600 rounded-lg cursor-crosshair
                 w-full max-w-[280px] aspect-square touch-none"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    />
    <Button onClick={clear} variant="outline" className="mt-4">
      <Eraser className="mr-2 h-4 w-4" />
      クリア
    </Button>
  </div>
```

> **PointerEvent を使用する理由**: マウスとタッチの両方を統一的に処理できる。`touch-none` で iOS のスクロールを抑制。

#### 2.3.4 `components/PredictionChart.tsx`

```
Props:
  predictions: Prediction[]

レンダリング:
  <div className="w-full max-w-md">
    {predictions.map(({ digit, probability }) => {
      const percentage = (probability * 100).toFixed(1);
      const isMax = この数字が最大確率かどうか;
      return (
        <div key={digit} className="flex items-center gap-2 mb-1">
          <span className="w-6 text-right font-mono text-lg">{digit}</span>
          <div className="flex-1 bg-gray-800 rounded h-6 overflow-hidden">
            <div
              className={`h-full rounded transition-all duration-300 ease-out
                         ${isMax ? "bg-blue-500" : "bg-gray-500"}`}
              style={{ width: `${probability * 100}%` }}
            />
          </div>
          <span className="w-16 text-right text-sm font-mono">{percentage}%</span>
        </div>
      );
    })}
  </div>
```

- `transition-all duration-300 ease-out` でバーの幅変更時に滑らかなアニメーション
- 最大確率の数字は `bg-blue-500`、それ以外は `bg-gray-500`

#### 2.3.5 `components/WarmupOverlay.tsx`

```
Props: なし（表示/非表示は親が制御）

レンダリング:
  <div className="fixed inset-0 z-50 flex flex-col items-center justify-center
                  bg-black/70 text-white">
    <Loader2 className="h-8 w-8 animate-spin" />  {/* lucide-react */}
    <p className="mt-4 text-lg">サーバー起動中...</p>
    <p className="mt-2 text-sm text-gray-400">初回アクセス時は30秒ほどかかる場合があります</p>
  </div>
```

### 2.4 カスタムフック詳細

#### 2.4.1 `hooks/useCanvas.ts`

```typescript
interface UseCanvasReturn {
  canvasRef: RefObject<HTMLCanvasElement>;
  handlePointerDown: (e: React.PointerEvent) => void;
  handlePointerMove: (e: React.PointerEvent) => void;
  handlePointerUp: () => void;
  clear: () => void;
  getImageAsBase64: () => string;
}

function useCanvas(): UseCanvasReturn {
  // isDrawing は useRef で管理（再レンダリング不要）
  // canvas 初期化は useEffect で実行（黒塗りつぶし）
}
```

#### 2.4.2 `hooks/usePredict.ts`

```typescript
interface UsePredictReturn {
  predictions: Prediction[];
  predict: (imageBase64: string) => void;
  resetPredictions: () => void;
  isLoading: boolean;
}

function usePredict(): UsePredictReturn {
  const [predictions, setPredictions] = useState<Prediction[]>(初期値);
  const [isLoading, setIsLoading] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const predict = useCallback((imageBase64: string) => {
    // 既存タイマーをクリア
    if (timerRef.current) clearTimeout(timerRef.current);

    // 500ms デバウンス
    timerRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const res = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imageBase64 }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "予測に失敗しました");
        }
        const data: PredictResponse = await res.json();
        setPredictions(data.predictions);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "エラーが発生しました");
      } finally {
        setIsLoading(false);
      }
    }, 500);
  }, []);

  // クリーンアップ
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { predictions, predict, resetPredictions, isLoading };
}
```

### 2.5 ヘルスチェック処理

#### `hooks/useServerHealth.ts`

```typescript
interface UseServerHealthReturn {
  isServerReady: boolean;
}

function useServerHealth(): UseServerHealthReturn {
  const [isServerReady, setIsServerReady] = useState(false);

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 20;  // 3秒 × 20 = 60秒
    let timer: NodeJS.Timeout;

    const check = async () => {
      try {
        const res = await fetch("/api/health", { signal: AbortSignal.timeout(5000) });
        if (res.ok) {
          setIsServerReady(true);
          return;
        }
      } catch { /* ignore */ }

      attempts++;
      if (attempts >= maxAttempts) {
        toast.error("サーバーに接続できません。しばらくしてからアクセスしてください。");
        return;
      }
      timer = setTimeout(check, 3000);
    };

    check();
    return () => clearTimeout(timer);
  }, []);

  return { isServerReady };
}
```

> **注意**: `toast` は `sonner` から import する。

---

## 3. バックエンド詳細設計

### 3.1 プロジェクト設定

#### `backend/requirements.txt`

```
fastapi==0.115.12
uvicorn[standard]==0.34.3
pillow==11.2.1
numpy==1.26.4
tflite-runtime==2.14.0
```

#### `backend/pyproject.toml`

```toml
[project]
name = "mnist-backend"
version = "1.0.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### 3.2 アプリケーションエントリ

#### `backend/app/main.py`

```python
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.predict import router as predict_router
from app.services.predictor import Predictor

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "model.tflite"
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    logger.info("モデルをロード中: %s", MODEL_PATH)
    app.state.predictor = Predictor(str(MODEL_PATH))
    logger.info("モデルロード完了")
    yield
    logger.info("アプリケーション終了")


def create_app() -> FastAPI:
    """FastAPI アプリケーションファクトリ"""
    app = FastAPI(
        title="手書き数字認識 API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(predict_router, prefix="/api")

    # 静的ファイル配信（本番用: Next.js ビルド成果物）
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()
```

### 3.3 ロギング設定

#### `backend/app/logging_config.py`

```python
import logging
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
```

- `main.py` の先頭で `setup_logging()` を呼び出す
- 画像データ（Base64）はログに出力しない（セキュリティ・サイズ考慮）

### 3.4 ルーター詳細

#### `backend/app/routers/predict.py`

```python
import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas.predict import PredictRequest, PredictResponse
from app.services.preprocessor import preprocess_image, PreprocessError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest, request: Request) -> PredictResponse:
    """手書き数字を認識して各数字の確率を返す"""
    logger.info("POST /api/predict を受信")

    try:
        image_array = preprocess_image(body.image)
    except PreprocessError as e:
        logger.warning("前処理エラー: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    predictor = request.app.state.predictor
    predictions = predictor.predict(image_array)

    top = max(predictions, key=lambda p: p.probability)
    logger.info("推論結果: digit=%d (%.1f%%)", top.digit, top.probability * 100)

    return PredictResponse(predictions=predictions)


@router.get("/health")
async def health() -> dict:
    """ヘルスチェック"""
    return {"status": "ok"}
```

### 3.5 スキーマ詳細

#### `backend/app/schemas/predict.py`

```python
from pydantic import BaseModel, Field, field_validator

# Base64 PNG の上限: 280x280 RGBA PNG ≈ 300KB → Base64 で約 400KB
# 余裕を持って 1MB（Base64文字列長 ≈ 1,398,102 文字）
MAX_IMAGE_LENGTH = 1_400_000


class PredictRequest(BaseModel):
    image: str = Field(
        ...,
        description="Base64エンコードされたPNG画像",
        max_length=MAX_IMAGE_LENGTH,
    )

    @field_validator("image")
    @classmethod
    def validate_image_format(cls, v: str) -> str:
        """Base64 PNG のプレフィクスチェック"""
        if v.startswith("data:"):
            # data:image/png;base64, プレフィクスの場合
            if not v.startswith("data:image/png;base64,"):
                raise ValueError("PNG 画像のみ対応しています")
        return v


class Prediction(BaseModel):
    digit: int = Field(..., ge=0, le=9)
    probability: float = Field(..., ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    predictions: list[Prediction] = Field(..., min_length=10, max_length=10)
```

### 3.6 画像前処理詳細

#### `backend/app/services/preprocessor.py`

```python
import base64
import io
import re

import numpy as np
from PIL import Image


class PreprocessError(Exception):
    """前処理に関するエラー"""
    pass


def preprocess_image(image_base64: str) -> np.ndarray:
    """
    Base64 PNG 画像を TFLite 入力形式に変換する。

    Parameters:
        image_base64: "data:image/png;base64,..." または 生Base64 文字列

    Returns:
        np.ndarray: shape (1, 28, 28, 1), dtype float32, 値域 [0.0, 1.0]

    Raises:
        PreprocessError: デコードや変換に失敗した場合
    """
    # 1. プレフィクス除去
    raw_b64 = _strip_data_uri_prefix(image_base64)

    # 2. Base64 デコード
    try:
        image_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise PreprocessError("Base64 デコードに失敗しました")

    # 3. PIL で画像を開く
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise PreprocessError("画像の読み込みに失敗しました")

    # 4. グレースケール変換
    image = image.convert("L")

    # 5. 28×28 にリサイズ
    image = image.resize((28, 28), Image.LANCZOS)

    # 6. NumPy 配列に変換 + 正規化
    arr = np.array(image, dtype=np.float32) / 255.0

    # 7. shape を (1, 28, 28, 1) に変換
    arr = arr.reshape(1, 28, 28, 1)

    return arr


def _strip_data_uri_prefix(data: str) -> str:
    """data:image/png;base64, プレフィクスがあれば除去"""
    pattern = r"^data:image/\w+;base64,"
    return re.sub(pattern, "", data)
```

**処理フロー図:**

```
"data:image/png;base64,iVBORw0KGgo..."
  ↓ _strip_data_uri_prefix()
"iVBORw0KGgo..."
  ↓ base64.b64decode()
b'\x89PNG\r\n...'  (バイト列)
  ↓ Image.open()
PIL.Image (280×280 RGBA)
  ↓ .convert("L")
PIL.Image (280×280 グレースケール)
  ↓ .resize((28, 28), LANCZOS)
PIL.Image (28×28 グレースケール)
  ↓ np.array() / 255.0
np.ndarray (28, 28) float32 [0.0〜1.0]
  ↓ .reshape(1, 28, 28, 1)
np.ndarray (1, 28, 28, 1) float32
```

### 3.7 TFLite 推論詳細

#### `backend/app/services/predictor.py`

```python
import numpy as np
from tflite_runtime.interpreter import Interpreter

from app.schemas.predict import Prediction


class Predictor:
    """TFLite モデルによる数字認識推論"""

    def __init__(self, model_path: str) -> None:
        self._interpreter = Interpreter(model_path=model_path)
        self._interpreter.allocate_tensors()
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

    def predict(self, image: np.ndarray) -> list[Prediction]:
        """
        Parameters:
            image: shape (1, 28, 28, 1), dtype float32

        Returns:
            10要素の Prediction リスト（digit=0〜9）
        """
        self._interpreter.set_tensor(
            self._input_details[0]["index"], image
        )
        self._interpreter.invoke()

        output = self._interpreter.get_tensor(
            self._output_details[0]["index"]
        )

        # softmax 適用（モデル出力が logits の場合）
        probabilities = self._softmax(output[0])

        return [
            Prediction(digit=i, probability=float(p))
            for i, p in enumerate(probabilities)
        ]

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """数値安定な softmax"""
        e = np.exp(x - np.max(x))
        return e / e.sum()
```

> **注意**: Keras モデルの最終層が `softmax` の場合、TFLite 変換後も softmax が含まれる。その場合 `_softmax()` は事実上恒等変換になるが、害はないためそのまま適用する。

### 3.8 静的ファイル配信の詳細

```
リクエストルーティング（FastAPI 内の優先順位）:
  1. /api/predict  → predict_router
  2. /api/health   → predict_router
  3. /*            → StaticFiles (Next.js ビルド成果物)
     - /index.html  → メインページ
     - /_next/*     → JS/CSS チャンク
     - /favicon.ico → ファビコン

StaticFiles の html=True により:
  - / → /index.html にフォールバック
  - /foo → /foo/index.html または /foo.html にフォールバック
```

---

## 4. 機械学習詳細設計

### 4.1 トレーニングスクリプト

#### `ml/train.py`

```python
"""
MNIST CNN モデルのトレーニングスクリプト

使用方法:
  cd ml
  pip install -r requirements.txt
  python train.py

出力:
  ml/model.keras — Keras 形式の学習済みモデル
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# ハイパーパラメータ
BATCH_SIZE = 128
EPOCHS = 10
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.1


def build_model() -> keras.Model:
    """CNN モデルを構築"""
    model = keras.Sequential([
        layers.Input(shape=(28, 28, 1)),

        layers.Conv2D(32, (3, 3), activation="relu"),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(64, (3, 3), activation="relu"),
        layers.MaxPooling2D((2, 2)),

        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(10, activation="softmax"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def load_data():
    """MNIST データセットをロード・前処理"""
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    # 正規化 + shape 変換
    x_train = x_train.astype("float32") / 255.0
    x_test = x_test.astype("float32") / 255.0
    x_train = x_train.reshape(-1, 28, 28, 1)
    x_test = x_test.reshape(-1, 28, 28, 1)

    # One-hot エンコーディング
    y_train = keras.utils.to_categorical(y_train, 10)
    y_test = keras.utils.to_categorical(y_test, 10)

    return (x_train, y_train), (x_test, y_test)


def create_data_augmentation():
    """データ拡張レイヤー"""
    return keras.Sequential([
        layers.RandomRotation(10 / 360),   # ±10度
        layers.RandomTranslation(0.1, 0.1), # ±10%
    ])


def main():
    (x_train, y_train), (x_test, y_test) = load_data()

    model = build_model()
    model.summary()

    # データ拡張
    augmentation = create_data_augmentation()

    # コールバック
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
        ),
    ]

    # トレーニング用データセット（データ拡張付き）
    train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
    train_dataset = train_dataset.shuffle(10000).batch(BATCH_SIZE)
    train_dataset = train_dataset.map(
        lambda x, y: (augmentation(x, training=True), y)
    )

    # バリデーション用データセット
    val_size = int(len(x_train) * VALIDATION_SPLIT)
    val_dataset = tf.data.Dataset.from_tensor_slices(
        (x_train[-val_size:], y_train[-val_size:])
    ).batch(BATCH_SIZE)

    # トレーニング
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=EPOCHS,
        callbacks=callbacks,
    )

    # テストデータで評価
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"\nテスト精度: {test_acc:.4f} ({test_acc * 100:.2f}%)")

    if test_acc < 0.95:
        print("警告: 精度が95%未満です")

    # モデル保存
    model.save("model.keras")
    print("モデルを model.keras に保存しました")


if __name__ == "__main__":
    main()
```

### 4.2 評価スクリプト

#### `ml/evaluate.py`

```python
"""
学習済みモデルの精度を評価するスクリプト

使用方法:
  python evaluate.py

終了コード:
  0 — 精度 95% 以上
  1 — 精度 95% 未満
"""
import sys
from tensorflow import keras


def main():
    model = keras.models.load_model("model.keras")
    (_, _), (x_test, y_test) = keras.datasets.mnist.load_data()

    x_test = x_test.astype("float32") / 255.0
    x_test = x_test.reshape(-1, 28, 28, 1)
    y_test = keras.utils.to_categorical(y_test, 10)

    _, accuracy = model.evaluate(x_test, y_test, verbose=0)
    print(f"テスト精度: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    if accuracy < 0.95:
        print("NG: 精度が95%未満です")
        sys.exit(1)

    print("OK: 精度目標を達成しています")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### 4.3 TFLite 変換スクリプト

#### `ml/export_tflite.py`

```python
"""
Keras モデルを TFLite に変換するスクリプト

使用方法:
  python export_tflite.py

出力:
  ml/model.tflite
  backend/app/models/model.tflite（コピー）
"""
import shutil
from pathlib import Path

import tensorflow as tf


def main():
    # Keras モデルをロード
    model = tf.keras.models.load_model("model.keras")

    # TFLite に変換
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    # ローカルに保存
    output_path = Path("model.tflite")
    output_path.write_bytes(tflite_model)
    print(f"TFLite モデルを {output_path} に保存しました")
    print(f"サイズ: {output_path.stat().st_size / 1024:.1f} KB")

    # backend にコピー
    backend_model_dir = Path("../backend/app/models")
    backend_model_dir.mkdir(parents=True, exist_ok=True)
    dest = backend_model_dir / "model.tflite"
    shutil.copy2(output_path, dest)
    print(f"バックエンドにコピー: {dest}")


if __name__ == "__main__":
    main()
```

#### `ml/requirements.txt`

```
tensorflow==2.17.1
```

---

## 5. デプロイメント詳細設計

### 5.1 Dockerfile（Render デプロイ用）

> ローカル開発では Docker を使用しない。Dockerfile は Render デプロイ専用。

```dockerfile
# ============================================
# Stage 1: フロントエンドビルド
# ============================================
FROM node:20-alpine AS frontend-build
WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build
# 出力先: /build/out/

# ============================================
# Stage 2: バックエンド（本番）
# ============================================
FROM python:3.11-slim
WORKDIR /app

# 依存関係インストール
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY backend/app/ ./app/

# フロントエンドビルド成果物
COPY --from=frontend-build /build/out/ ./static/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 ローカル開発（Docker 不使用）

フロントエンドとバックエンドを個別のターミナルで起動する。

```bash
# ターミナル 1: バックエンド
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ターミナル 2: フロントエンド
cd frontend
npm install
npm run dev
# http://localhost:3000 で起動
# /api/* は next.config.ts の rewrites で http://localhost:8000 にプロキシ
```

環境変数:
- `NEXT_PUBLIC_API_URL=http://localhost:8000`（デフォルト値として next.config.ts に設定済み）
- `LOG_LEVEL=DEBUG`（バックエンド開発時）

### 5.3 .gitignore

```gitignore
# ML モデル
*.tflite
*.keras
ml/__pycache__/

# Python
__pycache__/
*.pyc
.venv/

# Node.js
node_modules/
frontend/out/
frontend/.next/

# Docker
static/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

---

## 6. テスト詳細設計

### 6.1 フロントエンド テストケース

#### `__tests__/Canvas.test.tsx`

| # | テストケース | 検証内容 |
|---|---|---|
| 1 | キャンバスが描画される | `<canvas>` 要素が DOM に存在する |
| 2 | PointerDown + PointerMove で onDraw が呼ばれる | mock 関数の呼び出しを検証 |
| 3 | クリアボタンで描画がリセットされる | `clearRect` と `fillRect` の呼び出しを検証 |
| 4 | touch-none が設定されている | className に `touch-none` が含まれる |

#### `__tests__/PredictionChart.test.tsx`

| # | テストケース | 検証内容 |
|---|---|---|
| 1 | 全10桁が表示される | 0〜9 のラベルが DOM に存在する |
| 2 | 確率が%で表示される | "82.0%" のようなテキストが存在する |
| 3 | 最大確率の数字がハイライトされる | 最大値のバーに `bg-blue-500` クラスがある |
| 4 | 初期状態で全て 0% | 全バーの width が "0%" |

#### `__tests__/WarmupOverlay.test.tsx`

| # | テストケース | 検証内容 |
|---|---|---|
| 1 | オーバーレイが表示される | "サーバー起動中..." テキストが DOM に存在する |

#### `__tests__/usePredict.test.ts`

| # | テストケース | 検証内容 |
|---|---|---|
| 1 | predict() で API が呼ばれる | fetch mock が正しいパラメータで呼ばれる |
| 2 | 500ms デバウンスが機能する | 連続呼び出しで最後の1回のみ fetch される |
| 3 | API エラー時にトーストが表示される | toast.error mock が呼ばれる |
| 4 | resetPredictions() で初期値に戻る | predictions が全て 0 になる |

### 6.2 バックエンド テストケース

#### `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    """テスト用 FastAPI クライアント"""
    # テスト用のダミーモデルを作成する（または mock する）
    app = create_app()
    with TestClient(app) as c:
        yield c
```

#### `tests/test_predict_api.py`

| # | テストケース | 入力 | 期待結果 |
|---|---|---|---|
| 1 | 正常系: 有効な画像 | 280×280 黒背景の PNG (Base64) | 200, predictions に 10 要素 |
| 2 | 正常系: data URI 付き | "data:image/png;base64,..." | 200, 正常にパース |
| 3 | 異常系: 不正な Base64 | "not-valid-base64" | 400 |
| 4 | 異常系: 空文字列 | "" | 422 (Pydantic バリデーション) |
| 5 | 異常系: サイズ超過 | 2MB の Base64 文字列 | 422 (max_length) |
| 6 | 異常系: PNG 以外の data URI | "data:image/jpeg;base64,..." | 400 |
| 7 | ヘルスチェック | GET /api/health | 200, {"status": "ok"} |

#### `tests/test_preprocessor.py`

| # | テストケース | 入力 | 期待結果 |
|---|---|---|---|
| 1 | 正常系: 280×280 PNG | 有効な Base64 PNG | shape=(1,28,28,1), dtype=float32 |
| 2 | 正常系: data URI 付き | "data:image/png;base64,..." | 正常に処理される |
| 3 | 正常系: 値域確認 | 有効な PNG | 全要素が 0.0〜1.0 |
| 4 | 異常系: デコード失敗 | 不正な文字列 | PreprocessError |
| 5 | 異常系: 画像でないバイナリ | 非画像の Base64 | PreprocessError |

#### `tests/test_predictor.py`

| # | テストケース | 入力 | 期待結果 |
|---|---|---|---|
| 1 | 正常系: 推論実行 | shape=(1,28,28,1) の配列 | 10 要素の Prediction リスト |
| 2 | 確率の合計 ≒ 1.0 | 任意の入力 | sum(probabilities) ≈ 1.0 |
| 3 | digit が 0〜9 | 任意の入力 | digits = {0,1,...,9} |

---

## 7. 実装順序

TDD に従い、以下の順序で実装する。各ステップで「テスト作成 → テスト失敗確認 → 実装 → テスト成功確認」のサイクルを回す。

### Phase 1: ML モデル
1. `ml/requirements.txt` 作成
2. `ml/train.py` — モデル構築・トレーニング・保存
3. `ml/evaluate.py` — 精度評価（95% 以上の検証）
4. `ml/export_tflite.py` — TFLite 変換
5. モデルトレーニング実行 → `model.tflite` 生成

### Phase 2: バックエンド
6. `backend/` プロジェクト初期化（pyproject.toml, requirements.txt）
7. テスト: `test_preprocessor.py` → 実装: `preprocessor.py`
8. テスト: `test_predictor.py` → 実装: `predictor.py`
9. テスト: `test_predict_api.py` → 実装: `schemas/predict.py`, `routers/predict.py`, `main.py`
10. 結合テスト実行

### Phase 3: フロントエンド
11. `frontend/` プロジェクト初期化（Next.js + Tailwind CSS + shadcn/ui + Jest）
12. shadcn/ui コンポーネント追加（Button, Card, Progress, Skeleton, Sonner）
13. テスト: `Canvas.test.tsx` → 実装: `Canvas.tsx` + `useCanvas.ts`
14. テスト: `PredictionChart.test.tsx` → 実装: `PredictionChart.tsx`
15. テスト: `usePredict.test.ts` → 実装: `usePredict.ts`
16. テスト: `WarmupOverlay.test.tsx` → 実装: `WarmupOverlay.tsx`
17. `page.tsx` + `layout.tsx` 統合
18. 手動動作確認（ローカル）

### Phase 4: デプロイ
19. Dockerfile 作成（Render デプロイ用）
20. Render へデプロイ・動作確認

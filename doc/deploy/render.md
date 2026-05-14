# Render デプロイ手順

## 概要

本プロジェクトは Render の Web Service（Docker 環境）にデプロイする。  
FastAPI が Next.js の静的ビルド成果物と API の両方を単一コンテナで配信する。

```
[ ブラウザ ] ──HTTPS──> [ Render: Docker コンテナ ]
                              │
                         FastAPI (uvicorn)
                         ├── /api/predict  ← TFLite 推論
                         ├── /api/health   ← ヘルスチェック
                         └── /*            ← Next.js 静的ファイル
```

---

## 前提条件

- [ ] GitHub アカウント（リポジトリ公開済み）
- [ ] [Render](https://render.com) アカウント（無料プラン可）
- [ ] Python 3.11 がローカルにインストール済み
- [ ] Node.js 20 がローカルにインストール済み
- [ ] ML モデルのトレーニングが完了している（`ml/model.keras` が存在する）

---

## ステップ 1: ML モデルを TFLite に変換する

> モデルが既に `backend/app/models/model.tflite` に存在する場合はスキップ。

```bash
cd ml

# 仮想環境を作成して TensorFlow をインストール
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# model.keras → model.tflite に変換し、backend/app/models/ にコピー
python export_tflite.py
```

変換後、以下のファイルが存在することを確認する：

```
ml/model.tflite
backend/app/models/model.tflite   ← Docker イメージに含まれる
```

---

## ステップ 2: `backend/requirements.txt` に `tflite-runtime` を追加する

`tflite-runtime` がまだ追加されていない場合は追記する。

```
# backend/requirements.txt
fastapi==0.115.12
uvicorn[standard]==0.34.3
pillow==11.2.1
numpy==1.26.4
tflite-runtime==2.14.0
```

> **注意**: `tflite-runtime` は TensorFlow 本体より軽量な推論専用パッケージ。  
> Render の無料プランのメモリ制限（512MB）に収まるようにするため、`tensorflow` ではなく `tflite-runtime` を使用する。

---

## ステップ 3: Dockerfile を作成する

プロジェクトルート（`mnist/`）に `Dockerfile` を作成する。

```dockerfile
# ─────────────────────────────────────────
# Stage 1: フロントエンドのビルド
# ─────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# NODE_ENV=production で output: "export" を有効にして静的エクスポート
RUN NODE_ENV=production npm run build


# ─────────────────────────────────────────
# Stage 2: バックエンド（本番イメージ）
# ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Python 依存パッケージのインストール
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドのソースコードをコピー
COPY backend/ ./

# フロントエンドのビルド成果物を static/ にコピー
# FastAPI は backend/static/ を静的ファイルとして配信する
COPY --from=frontend-builder /app/frontend/out ./static

# ポート公開
EXPOSE 8000

# uvicorn でサーバー起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ステップ 4: `.gitignore` を更新する

`.gitignore` に以下のエントリが含まれていることを確認する。  
モデルファイルはリポジトリにコミットしないのがポリシーだが、  
**Render はリポジトリから Docker イメージをビルドするため、`backend/app/models/model.tflite` はコミットが必要**。

> ポリシーの例外事項として、`model.tflite` のみコミット対象にする。  
> `.gitignore` に `*.tflite` が含まれている場合は除外設定を追加する。

```gitignore
# ML / data artifacts（tflite は backend のみコミット対象）
*.keras
*.h5
ml/model.tflite
```

変更後、モデルファイルをコミットに含める：

```bash
git add backend/app/models/model.tflite
git commit -m "feat: add tflite model for deployment"
```

---

## ステップ 5: Dockerfile と更新内容を GitHub にプッシュする

```bash
cd mnist   # プロジェクトルート

git add Dockerfile backend/requirements.txt .gitignore
git commit -m "feat: add Dockerfile for Render deployment"
git push origin main
```

---

## ステップ 6: Render で Web Service を作成する

1. [Render Dashboard](https://dashboard.render.com) にログインする。
2. **New +** → **Web Service** をクリック。
3. **Connect a repository** で GitHub リポジトリを接続する。
4. 以下の設定を入力する：

| 項目 | 値 |
|---|---|
| **Name** | `mnist-app`（任意） |
| **Region** | `Oregon (US West)` または任意 |
| **Branch** | `main` |
| **Root Directory** | `mnist` |
| **Runtime** | `Docker` |
| **Dockerfile Path** | `./Dockerfile` |
| **Plan** | `Free` |

5. **Environment Variables** は不要（環境変数なしで動作する）。
6. **Advanced** → **Health Check Path** に `/api/health` を設定する。
7. **Create Web Service** をクリックしてデプロイを開始する。

---

## ステップ 7: デプロイの確認

Render のビルドログを確認しながら進行状況を監視する。

### ビルド正常終了のサイン

```
==> Building Docker image...
Successfully built <image-id>
==> Deploying...
==> Your service is live 🎉
```

### 動作確認

デプロイ完了後、Render が発行する URL（`https://mnist-app-xxxx.onrender.com` 形式）で確認する。

```bash
# ヘルスチェック
curl https://mnist-app-xxxx.onrender.com/api/health
# 期待レスポンス: {"status": "ok"}
```

ブラウザで URL を開き、手書きキャンバスが表示されることを確認する。

> **Free プランのコールドスタートについて**: 
> 無料プランではアイドル状態が続くとコンテナがスリープする。  
> 初回アクセス時は最大 30 秒程度かかる場合がある。  
> `WarmupOverlay` コンポーネントがサーバー起動中である旨を表示する。

---

## 再デプロイ（モデル更新時）

ML モデルを再トレーニングして更新する場合：

```bash
# 1. 新しいモデルを生成
cd ml
python train.py
python evaluate.py          # 精度 95% 以上を確認
python export_tflite.py     # backend/app/models/model.tflite を更新

# 2. コミット＆プッシュ（自動デプロイが走る）
cd ..
git add backend/app/models/model.tflite
git commit -m "feat: update tflite model"
git push origin main
```

`main` ブランチへのプッシュで Render が自動的に再ビルド・再デプロイする。

---

## トラブルシューティング

### ビルドエラー: `npm ci` が失敗する

`package-lock.json` が `package.json` と整合していない可能性がある。

```bash
cd frontend
npm install
git add package-lock.json
git commit -m "fix: update package-lock.json"
```

### ビルドエラー: `model.tflite` が見つからない

`backend/app/models/model.tflite` がリポジトリにコミットされているか確認する。

```bash
git ls-files backend/app/models/model.tflite
# 出力がない場合はコミットされていない
```

### 起動エラー: `No module named 'tflite_runtime'`

`backend/requirements.txt` に `tflite-runtime` が追加されているか確認し、再プッシュする。

### ヘルスチェック失敗でデプロイがロールバックされる

Render のログで FastAPI の起動エラーを確認する。  
主な原因はモデルファイルの読み込み失敗（パス不正）。  
`backend/app/main.py` の `MODEL_PATH` が `backend/app/models/model.tflite` を指していることを確認する。

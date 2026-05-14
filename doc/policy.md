# 実装ポリシー

## 進め方

- Phase ごとに立ち止まり、レビューを挟む。
  - Phase 1: ML モデル
  - Phase 2: バックエンド
  - Phase 3: フロントエンド
  - Phase 4: デプロイ

## TDD

- テストと実装をセットで作成し、最後にテスト実行結果を確認する。

## 環境

- Docker はローカル開発では使用しない。フロントエンドとバックエンドを個別に起動する。
- Docker は Render デプロイ時のみ使用する。
- ML トレーニングはローカル PC の CPU で実行する（GPU 不使用）。

## プロジェクト構成

- `mnist/` をプロジェクトルートとする。
- `mnist/frontend/`, `mnist/backend/`, `mnist/ml/` の monorepo 構成。
- `.tflite` / `.keras` ファイルは `.gitignore` に追加し、リポジトリにはコミットしない。

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

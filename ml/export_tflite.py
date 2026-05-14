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

    # 具体的な入力シグネチャを指定して ConcreteFunction を取得
    # （Keras 3 + TF 2.17 + Python 3.12 の互換性問題を回避）
    import numpy as np
    dummy_input = np.zeros((1, 28, 28, 1), dtype=np.float32)

    @tf.function(input_signature=[tf.TensorSpec(shape=[1, 28, 28, 1], dtype=tf.float32)])
    def predict(x):
        return model(x, training=False)

    concrete_func = predict.get_concrete_function()
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])
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

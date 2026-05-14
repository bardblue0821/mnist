"""TFLite モデルによる数字認識推論"""

import numpy as np

# tflite-runtime がインストールされている場合はそちらを使用
# なければ TensorFlow フルパッケージから Interpreter を取得
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

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

        # softmax 適用（モデル出力が logits の場合に備える）
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

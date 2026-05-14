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
        layers.RandomRotation(10 / 360),    # ±10度
        layers.RandomTranslation(0.1, 0.1),  # ±10%
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
    val_size = int(len(x_train) * VALIDATION_SPLIT)
    x_val, y_val = x_train[-val_size:], y_train[-val_size:]
    x_train_split, y_train_split = x_train[:-val_size], y_train[:-val_size]

    train_dataset = tf.data.Dataset.from_tensor_slices((x_train_split, y_train_split))
    train_dataset = train_dataset.shuffle(10000).batch(BATCH_SIZE)
    train_dataset = train_dataset.map(
        lambda x, y: (augmentation(x, training=True), y)
    )

    # バリデーション用データセット
    val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val)).batch(BATCH_SIZE)

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

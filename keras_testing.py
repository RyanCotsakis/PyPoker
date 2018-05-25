# import tensorflow as tf
# from keras.backend.tensorflow_backend import set_session

from keras.models import Sequential
from keras.layers import Dense, Dropout
import numpy as np


def start():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    set_session(tf.Session(config=config))
    print(1)

    model = Sequential([
        Dense(64, input_dim=15, activation='relu'),
        Dropout(0.2),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    x = np.random.random((2000, 15))
    y = (np.random.random((2000, 1))-0.5)*200
    model.fit(x, y, validation_split=0.1, epochs=20, batch_size=64, verbose=2)
    print('Done')


if __name__ == "__main__":
    start()

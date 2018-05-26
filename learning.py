from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout
import pickle
import numpy as np

PREFLOP_NAME = 'preflop'
FLOP_NAME = 'flop'
TURN_NAME = 'turn'
RIVER_NAME = 'river'

model_folder = './models/'
data_folder = './data/'

try:
    preflop_model = load_model(model_folder + PREFLOP_NAME + '.h5')
except IOError:
    preflop_model = None
try:
    flop_model = load_model(model_folder + FLOP_NAME + '.h5')
except IOError:
    flop_model = None
try:
    turn_model = load_model(model_folder + TURN_NAME + '.h5')
except IOError:
    turn_model = None
try:
    river_model = load_model(model_folder + RIVER_NAME + '.h5')
except IOError:
    river_model = None


def load_data(name):
    in_x = open(data_folder + 'x_' + name + '.pkl', 'rb')
    in_y = open(data_folder + 'y_' + name + '.pkl', 'rb')
    return pickle.load(in_x), pickle.load(in_y)


def create_model(name, epochs=128):
    x, y = load_data(name)
    n, m = x.shape
    assert n == y.size
    model = Sequential([
        Dense(64, input_dim=m, activation='relu'),
        Dropout(0.2),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(x, y, validation_split=0.1, epochs=epochs, batch_size=64, verbose=1)
    model.save(model_folder + name + '.h5')


def decision_parameter(x, model):
    if model is None:
        return 0

    fold = -x[1]  # This is the amount that the player pushed.
    x[0] = 0
    call = model.predict_on_batch(np.array([x]))
    x[0] = 1
    raise_1 = model.predict_on_batch(np.array([x]))
    x[0] = 2
    raise_2 = model.predict_on_batch(np.array([x]))
    x[0] = 3
    raise_3 = model.predict_on_batch(np.array([x]))

    params = [-1, 0, 1, 2, 3]
    actions = [fold, call, raise_1, raise_2, raise_3]
    return params[actions.index(max(actions))]


class Recorder:
    def __init__(self, name):
        self.name = name
        self._x = []
        self._y_before = []
        self._y_after = []
        self.x = []
        self.y_before = None
        self.y_after = None

    def save(self):
        out_x = open(data_folder + 'x_' + self.name + '.pkl', 'wb')
        out_y = open(data_folder + 'y_' + self.name + '.pkl', 'wb')
        pickle.dump(np.array(self._x), out_x)
        pickle.dump(np.array(self._y_after) - np.array(self._y_before), out_y)

    def add_to_list(self):
        for x in self.x:
            self._x.append(x)
            self._y_before.append(self.y_before)
            self._y_after.append(self.y_after)
        self.x = []
        self.y_before = None
        self.y_after = None

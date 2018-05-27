from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout
import pickle
import numpy as np

WATCH_AI = False

PREFLOP_NAME = 'preflop'
FLOP_NAME = 'flop'
TURN_NAME = 'turn'
RIVER_NAME = 'river'

model_folder = './models/simultaneous_'
data_folder = './data/simultaneous_'

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
    # data_folder = './data/'  # Comment this out after running 'start_games' once
    in_x = open(data_folder + 'x_' + name + '.pkl', 'rb')
    in_y = open(data_folder + 'y_' + name + '.pkl', 'rb')
    return pickle.load(in_x), pickle.load(in_y)


def create_model(name, epochs=200, model=None):
    x, y = load_data(name)
    n, m = x.shape
    assert n == y.size
    if model is None:
        print 'Could not find ' + model_folder + name + '.h5'
        model = Sequential([
            Dense(64, input_dim=m, activation='relu'),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    model.fit(x, y, validation_split=0.15, epochs=epochs, batch_size=128, verbose=2)
    model.save(model_folder + name + '.h5')
    return model


def decision_parameter(x, model):
    if model is None:
        return 0

    fold = -x[1]-x[2]/2.0
    x[0] = 0
    call = model.predict(np.array([x]))
    x[0] = 1
    raise_1 = model.predict(np.array([x]))
    x[0] = 2
    raise_2 = model.predict(np.array([x]))
    x[0] = 3
    raise_3 = model.predict(np.array([x]))

    params = [-1, 0, 1, 2, 3]
    actions = [fold, call, raise_1, raise_2, raise_3]

    if WATCH_AI:
        print '~\t' + '\t'.join([str(a) for a in actions])

    return params[actions.index(max(actions))]


class Recorder:
    def __init__(self, name):
        self.name = name
        self._x = []
        self._y_before = []
        self._y_after = []
        self.x = []
        self.y_before = []
        self.y_after = None

    def save(self):
        out_x = open(data_folder + self.name + '.pkl', 'wb')
        out_y = open(data_folder + self.name + '.pkl', 'wb')
        pickle.dump(np.array(self._x), out_x)
        pickle.dump(np.array(self._y_after) - np.array(self._y_before), out_y)

    def add_to_list(self):
        for x, y_before in zip(self.x, self.y_before):
            self._x.append(x)
            self._y_before.append(y_before)
            self._y_after.append(self.y_after)
        self.x = []
        self.y_before = []
        self.y_after = None

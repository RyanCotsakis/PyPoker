from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout
import pickle
import numpy as np
import random as rn

PREFLOP_NAME = 'preflop'
FLOP_NAME = 'flop'
TURN_NAME = 'turn'
RIVER_NAME = 'river'

model_folder = './models/ordered_'
data_folder = './data/ordered_'


def load_all_models():
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
    return preflop_model, flop_model, turn_model, river_model


def train_model(name, epochs=300):
    print "Training: " + name
    pf_model, f_model, t_model, r_model = load_all_models()
    if name == PREFLOP_NAME:
        model = pf_model
    elif name == FLOP_NAME:
        model = f_model
    elif name == TURN_NAME:
        model = t_model
    elif name == RIVER_NAME:
        model = r_model
    else:
        model = None

    # Load data
    try:
        in_x = open(data_folder + 'x_' + name + '.pkl', 'rb')
        in_y = open(data_folder + 'y_' + name + '.pkl', 'rb')
    except IOError as e:
        # print 'Using Alternate Data'
        # in_x = open('./data/x_' + name + '.pkl', 'rb')
        # in_y = open('./data/y_' + name + '.pkl', 'rb')
        raise e
    x, y = pickle.load(in_x), pickle.load(in_y)

    y = y - y.mean()
    n, m = x.shape
    assert n == y.size
    if model is None:
        print 'Could not find ' + model_folder + name + '.h5'
        model = Sequential([
            Dense(64, input_dim=m, activation='linear'),
            Dropout(0.2),
            Dense(64, activation='elu'),
            Dropout(0.2),
            Dense(32, activation='elu'),
            Dropout(0.2),
            Dense(1, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    model.fit(x, y, validation_split=0.15, epochs=epochs, batch_size=128, verbose=2)
    model.save(model_folder + name + '.h5')
    return model


def decision_parameter(x, model, verbose=False):
    """
    Use the net to make a decision. If no net, make a random choice
    :param x: list. Input to the net
    :param model: Neural Net
    :param verbose: Bool. Print the output of the net for each decision
    :return: int. best decision in {-1, 0, 1, 2, 3}
    """
    if model is None:
        d = rn.randint(-1,3)
        if verbose:
            print('~\tUsing random decision: {}'.format(d))
        return d

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

    if verbose:
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
        out_x = open(data_folder + 'x_' + self.name + '.pkl', 'wb')
        out_y = open(data_folder + 'y_' + self.name + '.pkl', 'wb')
        x = np.array(self._x)
        pot = x[:, 1] + x[:, 2]/2.0
        pot[pot == 0] = 1
        y = np.divide((np.array(self._y_after) - np.array(self._y_before)), pot)
        # y = y - y.mean()
        pickle.dump(x, out_x)
        pickle.dump(y, out_y)

    def add_to_list(self):
        for x, y_before in zip(self.x, self.y_before):
            self._x.append(x)
            self._y_before.append(y_before)
            self._y_after.append(self.y_after)
        self.x = []
        self.y_before = []
        self.y_after = None

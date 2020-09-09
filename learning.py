import pickle
import numpy as np
import random as rn

PREFLOP_NAME = 'preflop'
FLOP_NAME = 'flop'
TURN_NAME = 'turn'
RIVER_NAME = 'river'

model_folder = './models/ordered_'
data_folder = './data/ordered_'


class Model():

    def __init__(self, name):
        file = open(model_folder + name + '.pkl', 'rb')

        all_models = pickle.load(file)
        self.call_model = all_models[:,0]
        self.raise_1_model = all_models[:,1]
        self.raise_2_model = all_models[:,2]

    def call(self, x):
        return np.dot(self.call_model, x)

    def raise_1(self, x):
        return np.dot(self.raise_1_model, x)

    def raise_2(self, x):
        return np.dot(self.raise_2_model, x)

    def num_of_params(self):
        return len(self.call_model)


def load_all_models():
    try:
        preflop_model = Model(PREFLOP_NAME)
    except IOError:
        preflop_model = None
    try:
        flop_model = Model(FLOP_NAME)
    except IOError:
        flop_model = None
    try:
        turn_model = Model(TURN_NAME)
    except IOError:
        turn_model = None
    try:
        river_model = Model(RIVER_NAME)
    except IOError:
        river_model = None
    return preflop_model, flop_model, turn_model, river_model

def get_beta(X, Y):
    A = np.matmul(X.T, X)
    U, S, VT = np.linalg.svd(A)

    l = np.count_nonzero(S > 1e-2)
    U = U[:,:l]
    S = S[:l]
    S_inv = 1./S

    ret_val = np.matmul(U, np.diag(S_inv))
    ret_val = np.matmul(ret_val, U.T)
    ret_val = np.matmul(ret_val, X.T)
    ret_val = np.matmul(ret_val, Y)
    return ret_val.reshape((len(ret_val),1))





def train_model(name, data_name=None):
    if data_name is None:
        data_name = name
    print "Training: " + name

    pf_model, f_model, t_model, r_model = load_all_models()
    if name == PREFLOP_NAME:
        length_of_data = 12#pf_model.num_of_params()
    elif name == FLOP_NAME:
        length_of_data = 31#f_model.num_of_params()
    elif name == TURN_NAME:
        length_of_data = 32#t_model.num_of_params()
    elif name == RIVER_NAME:
        length_of_data = 33#r_model.num_of_params()

    # Load data
    try:
        in_x = open(data_folder + 'x_' + data_name + '.pkl', 'rb')
        in_y = open(data_folder + 'y_' + data_name + '.pkl', 'rb')
    except IOError as e:
        # print 'Using Alternate Data'
        # in_x = open('./data/x_' + name + '.pkl', 'rb')
        # in_y = open('./data/y_' + name + '.pkl', 'rb')
        raise e
    x_all, y_all = pickle.load(in_x), pickle.load(in_y)

    x = np.array([xi for xi in x_all if len(xi) == length_of_data], dtype='float')
    y = np.array([yi for xi, yi in zip(x_all,y_all) if len(xi) == length_of_data])

    y = y - y.mean()
    n, m = x.shape
    assert n == y.size

    x_call = np.array([xi[1:] for xi in x if xi[0] == 0])
    y_call = np.array([yi for xi, yi in zip(x,y) if xi[0] == 0])

    x_raise_1 = np.array([xi[1:] for xi in x if xi[0] == 1])
    y_raise_1 = np.array([yi for xi, yi in zip(x,y) if xi[0] == 1])

    x_raise_2 = np.array([xi[1:] for xi in x if xi[0] == 2])
    y_raise_2 = np.array([yi for xi, yi in zip(x,y) if xi[0] == 2])

    beta_call = get_beta(x_call, y_call)
    beta_raise_1 = get_beta(x_raise_1, y_raise_1)
    beta_raise_2 = get_beta(x_raise_2, y_raise_2)

    betas = np.hstack((beta_call, beta_raise_1, beta_raise_2))
    print betas
    file = open(model_folder + name + '.pkl', 'wb')
    pickle.dump(betas, file)


def decision_parameter(x_data, model, verbose=False):
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

    x = np.copy(x_data)
    x = x[1:]
    x = x.reshape((len(x),1))

    fold = 0
    call = model.call(x)
    raise_1 = model.raise_1(x)
    raise_2 = model.raise_2(x)

    params = [-1, 0, 1, 2]
    actions = [fold, call, raise_1, raise_2]

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
        pot = np.array([xi[2] for xi in x]) + np.array([xi[3] for xi in x])/2.0
        pot[pot == 0] = 1
        y = np.divide((np.array(self._y_after) - np.array(self._y_before)), pot)
        print "Saving " + str(len(y)) + " decisions."
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

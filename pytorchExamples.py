from __future__ import print_function
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as tfun
from myutils import *
from nnutils import *
from sklearn.utils import shuffle
from torch.autograd import Variable
import torchvision.models as models


def test_basics():
    x = torch.empty(5, 3)
    print(x)

    x = x.new_ones(5, 3)
    print(x)

    y = torch.rand(5, 3)
    print (y)
    print(x + y)
    print(x.add(y))

    res = torch.empty(5,3)
    res.new_ones(5,3)
    print('res a',res)
    torch.add(x,y,out=res)
    print('res b',res)

    a = np.ones(5)
    b = torch.from_numpy(a)
    print (type(b), b)
    print (type(a), a)
    c = b.numpy()
    print (type(c), c)

    print ('cuda?', torch.cuda.is_available())

# re-done base case logistic regression using bits of pytorch
def test_gaga_lr():
    # input specific setup
    data, yarr, features, fnames = getGagaData(maxrows=200, maxfeatures=2000, gtype=None, stopwords='english')
    xMatrix = shuffle(data, random_state=0)
    yArr = shuffle(np.array(yarr).reshape(-1,1), random_state=0)
    partition = int(.70*len(yArr))
    trainingX = xMatrix[:partition]
    trainingY = yArr[:partition]
    testX = xMatrix[partition:]
    testY = yArr[partition:]

    # wrap in torch functions
    dtype = torch.float
    x = torch.tensor(trainingX, dtype=dtype)
    y = torch.tensor(trainingY, dtype=dtype)  
    testx = torch.tensor(testX, dtype=dtype)
    testy = torch.tensor(testY, dtype=dtype)  

    # Randomly initialize weights
    torch.manual_seed(0)
    w1 = torch.randn(len(features),1, dtype=dtype)  # (n,1) shape

    learning_rate = 0.1
    for t in range(25000):
        h = x.mm(w1)               # each feature * weight
        y_pred = h.sigmoid()
        loss = (y_pred - y).pow(2).sum().item()  
        if (t % 5000 == 0):
            log.warn('loop %d, %.8f'%(t, loss))

        grad_w1 = x.t().mm(y_pred - y)
        w1 -= learning_rate * grad_w1

    print('training complete ', loss)
    print('test validation phase')

    h = testx.mm(w1)               # matrixMult or dot prod == same?
    y_pred = h.sigmoid().round()

    log.debug('ytest', pandas.DataFrame(testy.numpy()).head())
    log.debug('ypred', pandas.DataFrame(y_pred.numpy()).head())

    # Compute and print loss after rounding to 0/1's
    testDiffs = (y_pred - testy)
    p = pandas.DataFrame(testDiffs.numpy())
    log.debug('diffs', p.head())
    tests = len(p)
    correct = len(p[(p[0] == 0)])
    print('total correct/tests', correct, tests)
    print('correct % =', round((correct/tests)*100, 2))

# torch neural net manual
# @TODO this is work in progress, something wrong w/ backprop
def test_gaga_nn():
    dtype, device = torch.float,torch.device("cpu")
    F,H = 500,20 # features, hiddennodes
    D_in, D_out = F, 2  # 100 hidden nodes, 2 output nodes

    data, yarr, features, fnames = getGagaData(maxrows=500, maxfeatures=F, gtype=None, stopwords='english')
    xMatrix = shuffle(data, random_state=0)
    yArr = shuffle(yarr, random_state=0)

    partition = int(.70*len(yArr))
    trainingX = xMatrix[:partition]
    trainingY = yArr[:partition]
    testX = xMatrix[partition:]
    testY = yArr[partition:]

    # Create random input and output data
    x = torch.tensor(trainingX, dtype=dtype)
    y = torch.tensor(pd.get_dummies(trainingY).values, dtype=dtype)  # onehot y's
    testx = torch.tensor(testX, dtype=dtype)
    testy = torch.tensor(pd.get_dummies(testY).values, dtype=dtype)  # onehot y's

    # Randomly initialize weights, repeatable w/ seed
    np.random.seed(0)
    w1 = torch.tensor(np.random.rand(D_in, H), dtype=dtype, requires_grad=False)
    w2 = torch.tensor(np.random.rand(H, D_out), dtype=dtype, requires_grad=False)

    #gradient descent
    learning_rate = 0.005
    for t in range(1500):
        # Forward pass: compute predicted y
        h = x.mm(w1)               
        h_sig = h.sigmoid()        
        y_pred = h_sig.mm(w2)
        y_pred_sig = y_pred.sigmoid()

        loss = (y_pred_sig - y).pow(2).sum().item()  # item unwraps
        if (t % 200 == 0):
            print(t, loss)
            if (loss < 0.0001):
                break

        # Manual backprop routines
        grad_y_pred = 2.0*(y_pred_sig - y)  # dC/da = 2*(a-y)
        da_dz = h_sig.t().mm(1-h_sig)
        grad_w2 = h_sig.t().mm(grad_y_pred).t().mm(da_dz).t() # dC/dw2 = dz/dw2 * da/dz * dC/da

        grad_h_sig = h_sig*(1-h_sig)      
        grad_h = grad_h_sig.clone()
        grad_w1 = x.t().mm(grad_h)  # dC/dw1 = dC/dx * dx/dz * dz/dw2 * da/dz * dC/da ???
                                   # da/dz = sigmoid(a)*(1-sigmoid(a))
                                   # dC/da = 2*(h-y) at top layer
                                   # dz/dw1 = x
                                   # dz/dw2 = h

        if (t == 0):
            print('h_sig', grad_h)
            print('w2', grad_w2)

        w1 -= learning_rate * grad_w1
        w2 -= learning_rate * grad_w2

    print('training complete ',loss)
    print('test validation phase')

    h = testx.mm(w1)               # matrixMult or dot prod == same?
    h_sig = h.sigmoid()
    y_pred = h_sig.mm(w2).sigmoid()
    y_pred2 = torch.tensor(pd.get_dummies(y_pred.argmax(dim=1)).values, dtype=dtype)

#    print('ytest', pandas.DataFrame(testy.numpy()).head())
    print('ypred', pandas.DataFrame(y_pred.numpy()).head())
#    print('ypred2', pandas.DataFrame(y_pred2.numpy()).head())

    # Compute and print loss after rounding to 0/1's
    testDiffs = (y_pred2 - testy)
    p = pandas.DataFrame(testDiffs.numpy())
#    print('diffs', p.head())
    tests = len(p)
    correct = len(p[(p[0]==0) & (p[1]==0)])
    print('total correct/tests',correct,tests)
    print('correct % =', round((correct/tests)*100,2))
    print('hidden nodes %d'%H)

def test_gaga_nn_auto():
    dtype, device = torch.float, torch.device("cpu")
    F, H = 500, 20   # features
    D_in, D_out = F, 2  # 100 hidden nodes, 2 output nodes

    data, yarr, features, fnames = getGagaData(maxrows=500, maxfeatures=F, gtype=None, stopwords='english')
    
    xMatrix = shuffle(data, random_state=0)
    yArr = shuffle(yarr, random_state=0)

    partition = int(.70*len(yArr))
    trainingX = xMatrix[:partition]
    trainingY = yArr[:partition]
    testX = xMatrix[partition:]
    testY = yArr[partition:]

    x = torch.tensor(trainingX, dtype=dtype)
    y = torch.tensor(pd.get_dummies(trainingY).values, dtype=dtype)  # onehot y's
    testx = torch.tensor(testX, dtype=dtype)
    testy = torch.tensor(pd.get_dummies(testY).values, dtype=dtype)  # onehot y's

    # Randomly initialize weights, repeatable w/ seed
    np.random.seed(0)
    w1 = torch.tensor(np.random.rand(D_in, H), dtype=dtype, requires_grad=True)
    w2 = torch.tensor(np.random.rand(H, D_out), dtype=dtype, requires_grad=True)

    #gradient descent using autograd
    learning_rate = 0.005
    for t in range(1500):
        # Forward pass:2compute predicted y
        h = x.mm(w1).sigmoid()               # matrixMult or dot prod == same?
        y_pred = h.mm(w2).sigmoid()

        loss = (y_pred - y).pow(2).sum()  # item unwraps
        if (t % 200 == 0):
            print(t, loss.item())
            if (loss < 0.0001):
                break

        # autograd backprop
        loss.backward()  # goes thru graph
        if (t == 0):
            print('h_sig', h, h.grad)

        with torch.no_grad():  # halt autodiff 
            w1 -= learning_rate * w1.grad
            w2 -= learning_rate * w2.grad
            if (t == 0):
                print(w2.grad)
            w1.grad.zero_()
            w2.grad.zero_()

    print('training complete ', loss)
    print('test validation phase')

    h = testx.mm(w1).sigmoid()               # matrixMult or dot prod == same?
    y_pred = h.mm(w2).sigmoid()
    y_pred2 = torch.tensor(pd.get_dummies(y_pred.argmax(dim=1)).values, dtype=dtype)

#    print('ypred2', pandas.DataFrame(y_pred2.detach().numpy()).heaw1.grad #ut.grade and print loss after rounding to 0/1's
#    print('ytest', pandas.DataFrame(testy.numpy()).head())
    print('ypred', pandas.DataFrame(y_pred.detach().numpy()).head())
    testDiffs = (y_pred2 - testy)
    p = pandas.DataFrame(testDiffs.numpy())
#    print('diffs', p.head())
    tests = len(p)
    correct = len(p[(p[0] == 0) & (p[1] == 0)])
    print('total correct/tests', correct, tests)
    print('correct % =', round((correct/tests)*100, 2))
    print('hidden nodes %d' % H)

def test_pytorch_nn():
    net = Net()
    print(net)

    params = list(net.parameters())  
    print(len(params))   # list of major params matrices
    print(params[0].size())  # conv1's .weight

    input = torch.randn(1, 1, 32, 32)  # initial dummy input
    output = net(input)
    target = torch.arange(1, 11)  # a dummy target, for example
    target = target.view(1, -1)  # what is this ??
    criterion = nn.MSELoss()

    loss = criterion(output, target)
    print('loss tree',loss)
    print(loss.grad_fn)  # MSELoss
    print(loss.grad_fn.next_functions[0][0])  # Linear
    print(loss.grad_fn.next_functions[0][0].next_functions[0][0])  # ReLU

    # backprop
    loss.backward()
    print('conv1.bias.grad after backward')
    print(net.conv1.bias.grad)

    # sample backprop otpmizer
    import torch.optim as optim
    optimizer = optim.SGD(net.parameters(), lr=0.01) # learning rate 0.01 / for each parameter matrix

    # in your training loop:
    for epoch in range(500):
        optimizer.zero_grad()   # zero the gradient buffers
        output = net(input)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()    # Does the update
        if (epoch % 100 == 0):
            print('Epoch %s MSE %s' % (epoch, loss))

    print('conv1.bias.grad after optimizer')
    print(net.conv1.bias.grad)
    print ('--training done---')

    print('--test start---')
    test_input = torch.randn(1, 1, 32, 32)  # initial dummy input
    print ('input',test_input)
    print ('output/prediction',net.forward(test_input))   # returns activation

# apply higher level nn.Net lib to text
def test_pytorch_nn_gaga(t=1000):
    torch.set_printoptions(threshold=20, edgeitems=7)
    net = GagaNet()
    print(net) # print structure

    # get test data
    data, yarr, features, fnames = getGagaData(maxrows=500, maxfeatures=500, gtype=None, stopwords='english')
    
    xMatrix = shuffle(data, random_state=0)
    yArr = shuffle(yarr, random_state=0)
    partition = int(.70*len(yArr))
    trainingX = xMatrix[:partition]
    trainingY = yArr[:partition]
    testX = xMatrix[partition:]
    testY = yArr[partition:]

    input = torch.tensor(xMatrix, dtype=torch.float)  # m x 500
    target = torch.tensor(yArr, dtype=torch.float).view(-1,1)    # 1 x m
    test_input = torch.tensor(testX, dtype=torch.float)  # m x 500
    test_target =torch.tensor(testY, dtype=torch.float).view(-1,1)

    criterion = nn.MSELoss()
    output = net(input)
    loss = criterion(output, target)
    print('loss tree',loss)
    print(loss.grad_fn)  # MSELoss
    print(loss.grad_fn.next_functions[0][0])  # Linear

    # backprop
    loss.backward()
    print('net.inp.weight after backward')
    print(net.inp.weight)
 #   print(net.inp.weight.grad)

    # sample backprop otpmizer
    import torch.optim as optim
    optimizer = optim.SGD(net.parameters(), lr=0.01) # learning rate 0.01 / for each parameter matrix

    # in your training loop:
    for epoch in range(2500):
        optimizer.zero_grad()   # zero the gradient buffers
        output = net(input)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()    # Does the update
        if (epoch % 250 == 0):
            print('Epoch %s MSE %s' % (epoch, loss))

    print('net.inp.weight after gradient descent')
    print(net.inp.weight)
    print ('--training done---')

    test_res = net.forward(test_input)
    test_res_round = test_res.round()
    test_diff = test_res_round - test_target
    print ('output', test_res.view(1,-1))  
    print ('output rounded', test_res_round.view(1,-1))  
    print ('expected output', test_target.view(1,-1))  
    print ('err / total, %', test_diff.abs().sum().item(), len(test_diff),(len(test_diff)- test_diff.abs().sum().item()) / (len(test_diff)))

import argparse
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-t', help='batch size', type=int)
args = vars(parser.parse_args())

_t = args['t']

test_pytorch_nn_gaga(_t)
#test_pytorch_nn()
#print('--------------******-----------')
#test_gaga_nn_auto()
#test_gaga_lr()



import requests, pandas, io, numpy, argparse, math
import numpy as np
from nnutils import *
import featureEngineering as fe
from myutils import *
from mpmath import *
from gdsolvers import *
import logging as log
import inspect
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.utils import shuffle
import tensorflow as tf


def getGagaTfFormat(maxrows=500):
    xMatrix,yArr,features,fnames = fe.getGagaData(maxrows,stopwords='english')
    xMatrix = shuffle(xMatrix, random_state=0)   
    yArr = shuffle(yArr, random_state=0) 

    partition = int(.70*len(yArr))
    trainingMatrix = xMatrix[:partition]
    trainingY = yArr[:partition]
    testMatrix = xMatrix[partition:]
    testY = yArr[partition:]

    X = np.array(trainingMatrix)
    Y = trainingY
    from logisticRegression import reduceFeatures
    X,rfeatures = reduceFeatures(X, Y, features, 500)

    xs = X
    ys = np.array(Y).reshape(-1,1)  #col orient

    X = tf.constant(xs, dtype=tf.float32, name='X')
    y = tf.constant(ys, dtype=tf.float32, name='y')

    return X,y, features, rfeatures, testMatrix, testY  # testM/testY arne't in TF formats


def getGagaTfFormat2(maxrows=500):
    xMatrix,yArr,features,fnames = fe.getGagaData(maxrows,stopwords='english')
    xMatrix = shuffle(xMatrix, random_state=0)   
    yArr = shuffle(yArr, random_state=0) 

    partition = int(.70*len(yArr))
    trainingX = xMatrix[:partition]
    trainingY = yArr[:partition]
    testX = xMatrix[partition:]
    testY = yArr[partition:]

    trainingX = np.array(trainingX)
    from logisticRegression import reduceFeatures
    trainingX, rfeatures = reduceFeatures(trainingX, trainingY, features, 500)

    # reduce testSet to same features
    df = pandas.DataFrame(testX, columns=features)
    testX = df[rfeatures].as_matrix()

    # convert to TensorFlow formats
    trainingY = pd.get_dummies(trainingY)
    testY = pd.get_dummies(testY)

    return trainingX, trainingY, features, rfeatures, testX, testY


def test_gaga_tensor():
    tf.reset_default_graph()
    n_epochs = 400
    learning_rate = 0.01

    X,y,features,rfeatures,testMatrix,testY = getGagaTfFormat()
    m = len(testMatrix[0])
    n = len(rfeatures)
    guesses = np.array([0.01]*n,dtype='float32' ).reshape(-1,1)  # col orient
    theta = tf.Variable(tf.constant(guesses), name='theta')
    y_pred = tf.sigmoid(tf.matmul(X, theta, name='predictions'))

    print ('-------xxx')
    print (X)
    print(y)
    print ('-------xxx')

    with tf.name_scope("loss"):
        error = y_pred - y  # vs ll ?
        ll = tf.reduce_mean(tf.losses.log_loss(y,y_pred), name='log_loss')  # -log(x) or -log(1-x) ....

    with tf.name_scope("gradients"):
        gradients = 2.0/m * tf.matmul(tf.transpose(X), error)  # vs ll vs error 
        training_op = tf.assign(theta, theta - learning_rate * gradients)   # what is this

    ll_summary = tf.summary.scalar('log_loss',ll)
    file_writer = tf.summary.FileWriter(getLogDir(),tf.get_default_graph())
    init = tf.global_variables_initializer()

    with tf.Session() as sess:
        sess.run(init)
        for epoch in range(n_epochs):
            if (epoch % 25 == 0):
                print('Epoch %s Log_Loss %s'%(epoch, ll.eval()))
                summary_str = ll_summary.eval()  # bug
                step = epoch
                file_writer.add_summary(summary_str, step)
            sess.run(training_op)   # whats an opp
        best_theta = theta.eval()
    print(gf(best_theta))   # scores should be similar to sckit and grad5 solver
    file_writer.close()

    # reduce test set similarly (note below works because we know full set of train+test features ahead of time)    
    df = pandas.DataFrame(testMatrix, columns=features)   # new df w/ column names
    X = df[rfeatures].as_matrix()                # filter out only rfeatures

    testRes = np.dot(X, best_theta)
    testResRound = [round(sigmoid(x),0) for x in testRes]
    testDiffs = np.array(testResRound) - np.array(testY)
    log.warn ('raw results %s '%(gf(testRes)))
    log.warn ('sig results %s'%gf([sigmoid(x) for x in testRes]))
    log.warn ('0|1 results %s'%([round(sigmoid(x)) for x in testRes]))
    log.warn (testDiffs)
    log.error ('mymodel errors: %s / %s = %f'%(sum([abs(x) for x in testDiffs]),len(testY),sum([abs(x) for x in testDiffs])/len(testY)))

    return best_theta

def test_gaga_nn_tensor():
    tf.enable_eager_execution()
    tf.reset_default_graph()
    X,y,features,rfeatures,testMatrix,testY = getGagaTfFormat()

    # boilerplate NN
    n_epocs = 10  #40
    batch_size = 50
    learning_rate = 0.01
 
    ## NN setup phase
#    n_inputs = 2000  # features/words
    n_hidden1 = 200
    n_outputs = 2

    print ('-------')
    print ('X',X)
    print('y.shape',y.shape)
    
    print ('-------')

    with tf.name_scope("dnn"):
        hidden1 = neuron_layer_eager(X, n_hidden1, "hidden1", activation=tf.nn.relu)
        logits = neuron_layer_eager(hidden1, n_outputs, "outputs", )
        print ('logits',logits.shape)

    with tf.name_scope("loss"):
        xentropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=logits)  #bug
        loss = tf.reduce_mean(xentropy, name="loss")
        print ('loss',loss)

    with tf.name_scope("train"):
        optimizer = tf.train.GradientDescentOptimizer(learning_rate)
        training_op = optimizer.minimize(loss)
        print('training_op',training_op)

    with tf.name_scope("eval"):
        correct = tf.nn.in_top_k(logits, y, 1)
        accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))
        print('eval',accuracy)

    ## exec run phase
    print ('exec run')
    init = tf.global_variables_initializer()
    file_writer = tf.summary.FileWriter(getLogDir(),tf.get_default_graph())
    saver = tf.train.Saver()

    with tf.Session() as sess:
        init.run()
        for epoc in range(n_epocs):
            sess.run(training_op)  
            acc_train = accuracy.eval()
            print (epoc, "train accuracy:", acc_train)
        save_path = saver.save(sess, "./tf_logs/my_model_final.ckpt")
#    file_writer.add_summary(summary_str, step)
    file_writer.close()
    # not workign

def test_gaga_nn2_tensor():
    tf.reset_default_graph()

    Xtrain, ytrain, features, rfeatures, Xtest, ytest = getGagaTfFormat2()

    # Plot the loss function over iterations
    num_hidden_nodes = [5, 10, 20, 50, 100]
    loss_plot = {5: [], 10: [], 20: [], 50: [], 100: []}
    weights1 = {5: None, 10: None, 20: None, 50: None, 100: None}
    weights2 = {5: None, 10: None, 20: None, 50: None, 100: None}
    num_iters = 2000

    plt.figure(figsize=(12, 8))
    for hidden_nodes in num_hidden_nodes:
        weights1[hidden_nodes], weights2[hidden_nodes] = create_train_model(
            hidden_nodes, num_iters, Xtrain, ytrain, loss_plot)
        plt.plot(range(num_iters),
                 loss_plot[hidden_nodes], label="nn: %d-%d-2" % (len(rfeatures),hidden_nodes))

    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend(fontsize=12)

    # Evaluate models on the test set (7 test examples, 500 features, 2 outputs)
    X = tf.placeholder(shape=(len(ytest), len(rfeatures)), dtype=tf.float64, name='X')
    y = tf.placeholder(shape=(len(ytest), 2), dtype=tf.float64, name='y')

    for hidden_nodes in num_hidden_nodes:
        # Forward propagation
        W1 = tf.Variable(weights1[hidden_nodes])
        W2 = tf.Variable(weights2[hidden_nodes])
        A1 = tf.sigmoid(tf.matmul(X, W1))
        y_est = tf.sigmoid(tf.matmul(A1, W2))

        # Calculate the predicted outputs
        init = tf.global_variables_initializer()
        with tf.Session() as sess:
            sess.run(init)
            y_est_np = sess.run(y_est, feed_dict={X: Xtest, y: ytest})

        # Calculate the prediction accuracy
        correct = [estimate.argmax(axis=0) == target.argmax(axis=0)
                   for estimate, target in zip(y_est_np, ytest.as_matrix())]
        accuracy = 100 * sum(correct) / len(correct)
        print('Network architecture %d-%d-2, accuracy: %.2f%%' % (len(rfeatures), hidden_nodes, accuracy))
#    plt.show()

if __name__ == "__main__":
    log.getLogger().setLevel(log.INFO)
    # test_gaga_tensor()
    test_gaga_nn2_tensor()


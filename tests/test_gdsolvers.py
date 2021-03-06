# test test
from myutils import *
from gdsolvers import *
import inspect
import numpy as np
from sklearn.metrics import *

def test_dummy():
    print (inspect.currentframe().f_code.co_name)
    assert (1+3) == 4

def test_evalSumF2():
    print (inspect.currentframe().f_code.co_name)
    x0,x1,t0,t1,y = sp.symbols('x0,x1,t0,t1,y')
    f = (x0*t0 + x1*t1 - y)**2  # sum-square-error (MSE) of mx+b
    xs = [x0,x1]
    trainingMatrix = [[1,5],[1,10]]
    f = sp.diff(f,x0)
    s = evalSumF2(f,xs,trainingMatrix,[10,15])
    assert(str(s) == "1.0*t0*(t0 + 5*t1 - 10) + 1.0*t0*(t0 + 10*t1 - 15)")

def test_evalSumF2_1():
    print (inspect.currentframe().f_code.co_name)
    x0,x1,t0,t1,y = sp.symbols('x0,x1,t0,t1,y')
    f = (x0*t0 + x1*t1 - y)**2  # sum-square-error (MSE) of mx+b
    xs = [x0,x1]
    trainingMatrix = [[1,2],[1,4]]
    log.warn (f)
    f = sp.diff(f,x1)
    log.warn (f)
    s = evalSumF2(f,xs,trainingMatrix,[10,11])
    log.warn (s)
    assert(str(s) == "1.0*t1*(t0 + 2*t1 - 10) + 1.0*t1*(t0 + 4*t1 - 11)")

def test_evalPartialDeriv2():
    print (inspect.currentframe().f_code.co_name)
    df = setupBrainData(4)  # 'gender', 'age_range', 'head_size', 'brain_weight'
    df['bias'] = 1
    trainingMatrix = df[['bias','head_size']]
    trainingMatrix = trainingMatrix.as_matrix()
    yArr = df[['brain_weight']].as_matrix()
    guesses = [0*len(yArr)]

    ts = sp.symbols('t:'+str(len(trainingMatrix[0])))  #theta weight/parameter array
    xs = sp.symbols('x:'+str(len(trainingMatrix[0])))  #feature array

    log.warn (trainingMatrix)
    log.warn (ts)
    log.warn (xs)

    y = sp.symbols('y')
    f = ts[0]*xs[0] + ts[1]*xs[1]
    cFunc = (f - y)**2  # error squared
    
    log.warn('init guesses %s',str(guesses))
    log.error('init func: %s, training size: %d' %(str(f),len(trainingMatrix)))
    log.debug('ts: %s / xs: %s',ts,xs)

    costF = evalSumF2(cFunc,xs,trainingMatrix,yArr)  # cost fun evaluted for testData
    cost = 0.0+costF.subs(zip(ts,guesses))  
    log.warn ('costF ',costF)
    log.warn ('cost ',cost)
    
    pds = []
    for theta in ts:
        pd = evalPartialDeriv2(f,theta,ts,xs,trainingMatrix,guesses,yArr)
        log.warn ('deriv %s of %s = %f'%(str(f),str(theta),pd))
        pds.append(pd)

    assert(pds[0] == 1.0)
    assert(pds[1] == 4072.0)

def test_grad_descent_sympy_mse():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,4],[1,10],[1,20]])
    yArr = [8,18,42]
    guesses = [0.01]*len(yArr)

    ts = sp.symbols('t:'+str(len(trainingMatrix[0])))  #theta weight/parameter array
    xs = sp.symbols('x:'+str(len(trainingMatrix[0])))  #feature array

    y = sp.symbols('y')
    f = ts[0]*xs[0] + ts[1]*xs[1]
    cFunc = (f - y)**2  # error squared

    costF = evalSumF2(cFunc,xs,trainingMatrix,yArr)  # cost fun evaluted for testData
    cost = 0.0+costF.subs(zip(ts,guesses))  
    log.warn('costF %s'%(str(costF)))
    log.warn('cost %s'%(str(cost)))

    log.warn('init guesses %s',str(guesses))
    log.error('init func: %s, training size: %d' %(str(f),len(trainingMatrix)))
    log.warn('ts: %s / xs: %s',ts,xs)

    gs = grad_descent_sympy(f,costF,trainingMatrix,yArr,step=0.005,loop_limit=100)    
    log.warn('scaled A: %f'%(gs[0]))
    log.warn('scaled B: %f'%(gs[1]))

    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == -0.28)
    assert(round(gs[1],2) == 2.06)    

def test_grad_descent_sympy_bs1(bs=1):
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8]])
    yArr = [14,16,18,20,21,22,22]

    ts = sp.symbols('t:'+str(len(trainingMatrix[0])))  #theta weight/parameter array
    xs = sp.symbols('x:'+str(len(trainingMatrix[0])))  #feature array

    y = sp.symbols('y')
    f = ts[0]*xs[0] + ts[1]*xs[1]
    cFunc = (f - y)**2  # error squared

    costF = evalSumF2(cFunc,xs,trainingMatrix,yArr)  # cost fun evaluted for testData
    log.warn('costF %s'%(str(costF)))

    log.error('init func: %s, training size: %d' %(str(f),len(trainingMatrix)))
    log.warn('ts: %s / xs: %s',ts,xs)

    gs = grad_descent_sympy(f,costF,trainingMatrix,yArr,step=0.03,loop_limit=50, batchSize=bs)    
    log.warn('scaled A: %f'%(gs[0]))
    log.warn('scaled B: %f'%(gs[1]))

    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == 4.94)
    assert(round(gs[1],2) == 2.61)    

def test_grad_descent5_mse():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,4],[1,10],[1,20]])  # 2 features
    yArr = [8,18,42]

    gs = grad_descent5(lambda y,x: x-y,mean_squared_error,trainingMatrix,yArr,step=0.005,loop_limit=500)    
    log.warn('final: %s'%gs)
    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == -1.20)
    assert(round(gs[1],2) == 2.12)    

def test_grad_descent5_mse_vs_mae():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,4],[1,10],[1,20]])  # 2 features
    yArr = [8,18,42]

    gs = grad_descent5(lambda y,x: x-y,mean_absolute_error,trainingMatrix,yArr,step=0.005,loop_limit=500)    
    gs1 = grad_descent5(lambda y,x: x-y,mean_squared_error,trainingMatrix,yArr,step=0.005,loop_limit=500)    
    log.warn('final: %s'%gs)
    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == round(gs1[0],2))
    assert(round(gs[1],2) == round(gs1[1],2))
    assert(round(gs[0],2) == -1.20)
    assert(round(gs[1],2) == 2.12)    

def test_grad_descent_logr():
    print (inspect.currentframe().f_code.co_name)
    X = np.asarray([
        [0.50],[0.75],[1.00],[1.25],[1.50],[1.75],[1.75],
        [2.00],[2.25],[2.50],[2.75],[3.00],[3.25],[3.50],
        [4.00],[4.25],[4.50],[4.75],[5.00],[5.50]])
    ones = np.ones(X.shape)  
    X = np.hstack([ones, X])  # makes it [[1,.5][1,.75]...]
    Y = np.array([0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1])
    gs = grad_descent_logr(X, Y)
    log.warn('grad_logr %s'%gs)

    gs2,intercept = sklearn_logr_comp(X,Y)
    log.warn ('scikit log_reg coef: %s'%gs2)
    log.warn ('scikit log_reg intercept %s'%intercept)

def test_grad_descent5_logr():
    print (inspect.currentframe().f_code.co_name)
    X = np.asarray([
        [0.50],[0.75],[1.00],[1.25],[1.50],[1.75],[1.75],
        [2.00],[2.25],[2.50],[2.75],[3.00],[3.25],[3.50],
        [4.00],[4.25],[4.50],[4.75],[5.00],[5.50]])
    ones = np.ones(X.shape)  
    X = np.hstack([ones, X])  # makes it [[1,.5][1,.75]...]
    Y = np.array([0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1])

    gs = grad_descent5(lambda y,x: sigmoid(x)-y,log_loss,X,Y,step=0.5,step_limit=0.000001,loop_limit=500, batchSize=20)    
    log.warn('final: %s'%gs)
    assert(round(gs[0],2) == -4.02)
    assert(round(gs[1],2) == 1.48)

    ## just for ref:
    gs2,intercept = sklearn_logr_comp(X,Y)
    log.warn ('scikit log_reg coef: %s'%gs2)
    log.warn ('scikit log_reg intercept %s'%intercept)

def test_grad_descent5_logr_vs_ref():
    print (inspect.currentframe().f_code.co_name)
    X = np.asarray([
        [0.50],[0.75],[1.00],[1.25],[1.50],[1.75],[1.75],
        [2.00],[2.25],[2.50],[2.75],[3.00],[3.25],[3.50],
        [4.00],[4.25],[4.50],[4.75],[5.00],[5.50]])
    ones = np.ones(X.shape)  
    X = np.hstack([ones, X])  # makes it [[1,.5][1,.75]...]
    Y = np.array([0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1])

    gs = grad_descent5(lambda y,x: sigmoid(x)-y,log_loss,X,Y,step=0.1,step_limit=0.0000001,loop_limit=2000, batchSize=20)    
    log.warn('grad_descent5: %s'%gs)

    gs2 = grad_descent_logr(X, Y, 2000, 0.1)
    log.warn('grad_descent_logr %s'%gs2)

    gs3,intercept = sklearn_logr_comp(X,Y)
    log.warn ('scikit log_reg coef: %s'%gs3)
    log.warn ('scikit log_reg intercept %s'%intercept)

    assert(round(gs[0],1) == round(gs2[0],1))
    assert(round(gs[1],1) == round(gs2[1],1))

def test_grad_descent_mse():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,4],[1,10],[1,20]])  # 2 features
    yArr = [8,18,42]

    gs = grad_descent_linr_mse(trainingMatrix, yArr, 1000,0.005)
    log.warn('final: %s'%gs)
    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    from sklearn.linear_model import LinearRegression
    log_reg = LinearRegression()
    log_reg.fit(X,Y)
    log.warn ('scikit log_reg coef: %s'%log_reg.coef_)
    log.warn ('scikit log_reg intercept %s'%log_reg.intercept_)

    assert(round(gs[0],2) == -1.58)
    assert(round(gs[1],2) == 2.14)    

# sympy perf comparisoin vs grad5 solver
def test_grad_descent_sympy_vs_grad5():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8]])
    yArr = [14,16,18,20,21,22,22]

    ts = sp.symbols('t:'+str(len(trainingMatrix[0])))  #theta weight/parameter array
    xs = sp.symbols('x:'+str(len(trainingMatrix[0])))  #feature array
    y = sp.symbols('y')
    f = ts[0]*xs[0] + ts[1]*xs[1]
    cFunc = (f - y)**2  # error squared

    costF = evalSumF2(cFunc,xs,trainingMatrix,yArr)  # cost fun evaluted for testData
    log.warn('costF %s'%(str(costF)))
    log.error('init func: %s, training size: %d' %(str(f),len(trainingMatrix)))
    log.warn('ts: %s / xs: %s',ts,xs)

    gs, t1 = time_fn(grad_descent_sympy,f,costF,trainingMatrix,yArr,step_limit=-1,step=0.03,loop_limit=1000, batchSize=10)
    log.warn('final: %s %s'%(gs,t1))
    gs2, t2 = time_fn(grad_descent5,lambda y,x: x-y,mean_squared_error,trainingMatrix,yArr,step_limit=-1,step=0.03,loop_limit=1000,batchSize=10)
    log.warn('final: %s %s'%(gs2,t2))

    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],1) == round(gs2[0],1))
    assert(round(gs[1],1) == round(gs2[1],1))
 
    gs, t3 = time_fn(grad_descent_sympy,f,costF,trainingMatrix,yArr,step_limit=-1,step=0.03,loop_limit=5000, batchSize=1)
    gs2, t4 = time_fn(grad_descent5,lambda y,x: x-y,mean_squared_error,trainingMatrix,yArr,step_limit=-1,step=0.03,loop_limit=5000,batchSize=1)
 
    log.error('symbolic  time (5000 loops, bs 1: %s'%t3)
    log.error('g5 matrix time (5000 loops, bs 1: %s'%t4)
    log.error('symbolic  time (1000 loops, bs 10: %s'%t1)
    log.error('g5 matrix time (1000 loops, bs 10: %s'%t2)
    log.error('multiplier: %s'%(t1/t2))
    log.error('multiplier: %s'%(t3/t4))

def test_grad_descent_mse_2():
    print (inspect.currentframe().f_code.co_name)
    trainingMatrix = np.array([[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8]])
    yArr = [14,16,18,20,21,22,22]

    gs = grad_descent_linr_mse(trainingMatrix, yArr, 1000, 0.005)
    log.warn('final: %s'%gs)
    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == 9.04)
    assert(round(gs[1],2) == 1.91)    

def test_grad_descent5_mse_2():
    print (inspect.currentframe().f_code.co_name)

    trainingMatrix = np.array([[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8]])
    yArr = [14,16,18,20,21,22,22]
    gs = grad_descent5(lambda y,x: x-y,mean_squared_error,trainingMatrix,yArr,step=0.005,loop_limit=1000)    
    log.warn('final: %s'%gs)
    X = np.asmatrix(trainingMatrix)
    Y = yArr
    log.warn ('target Linear Reg sol: %s'% str((X.T.dot(X)).I.dot(X.T).dot(Y)))

    assert(round(gs[0],2) == 9.04)
    assert(round(gs[1],2) == 1.91)    

if __name__ == "__main__":
    log.getLogger().setLevel(log.WARN)
    test_evalSumF2()
    test_evalSumF2_1()
    test_evalPartialDeriv2()
    test_grad_descent_sympy_mse()
    test_grad_descent_sympy_bs1()
    test_grad_descent_logr() 
    test_grad_descent_mse()
    test_grad_descent_mse_2()
    test_grad_descent5_mse_vs_mae()
    test_grad_descent5_mse()     
    test_grad_descent5_mse_2()
    test_grad_descent5_logr()
    test_grad_descent5_logr_vs_ref()
    test_grad_descent_sympy_vs_grad5()

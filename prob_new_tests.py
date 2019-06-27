#!/usr/bin/env python
import math
import warnings
import numpy as np
import pandas as pd
import math
from scipy.stats import mode
from timeit import default_timer
from importlib import import_module
from contextlib import contextmanager


case = "discrete"
aps = False

# Problem parameters
D = 100
c = 50
e = 50
h = 0.1
k = 0.1

# Discretization steps
stepA = 0.01
stepD = 0.01

a_values = np.arange(0, 1, stepA)
d_values = np.arange(0, 1, stepD)


f = lambda d, theta: (1-theta)*D - c*d
g = lambda a, theta: theta*D - e*a

eps = 0.01 # To avoida alpha and beta to be 0
alpha = lambda d,a: a - d + 1 + eps
beta  = lambda d,a: d - a + 1 + eps

prob   = lambda d, a, size=1: np.random.beta( alpha(d,a), beta(d,a), size=size )

d_util = lambda d, theta: 1.0 - np.exp( -h * f(d,theta) )
a_util = lambda a, theta: np.exp(-k * g(a,theta) )

if case == "discrete":
    ##
    a_values = np.arange(0, 1, 0.001)
    d_given = 0.9
    a_optimal = 0.999
    mcmc_iters = 10000
    N_inner = 1000000
    burnin = 0.5
    ################################################################################
    # MC for attacker. Discrete case
    ################################################################################
    psi_a = np.zeros(len(a_values), dtype=float)

    start = default_timer()
    ##
    for j, a in enumerate(a_values):
        theta_a = prob(d_given, a, size=mcmc_iters)
        psi_a[j] = a_util(a, theta_a).mean()
    ##
    end = default_timer()
    print('Elapsed MC time: ', end-start)
    a_opt = a_values[psi_a.argmax()]
    print('Optimal MC attack for given defense', a_opt)

if aps:
    ################################################################################
    # APS for attacker. Discrete case
    ################################################################################
    def propose(x_given, x_values, prop=0.1):
        tochoose = int(len(x_values)*prop)
        coin = np.random.choice([0,1])
        idx = list(x_values).index(x_given)
        if coin == 0:
            start = idx+1
            end = start + tochoose
            if end >= len(x_values):
                candidates = np.concatenate((x_values[start:], a_values[:end-len(x_values)]))
            else:
                candidates = x_values[start:end]
        else:
            start = idx
            end = start-tochoose
            if end < 0:
                candidates = np.concatenate((x_values[:start][::-1], x_values[end:][::-1]))
            else:
                candidates = x_values[end:start][::-1]
        return( np.random.choice(candidates) )


    #def propose(x_given, x_values):
    #    if x_given == x_values[0]:
    #        return( np.random.choice([x_values[1], x_values[-1]],
    #        p=[0.5, 0.5]) )

    #    if x_given == x_values[-1]:
    #        return( np.random.choice([x_values[0], x_values[-2]],
    #        p=[0.5, 0.5]) )

    #    idx = list(x_values).index(x_given)
    #    return( np.random.choice([x_values[idx+1], x_values[idx-1]],
    #    p=[0.5, 0.5]) )

    a_sim = np.zeros(N_inner, dtype = float)
    a_sim[0] = np.random.choice(a_values)
    theta_sim = prob(d_given, a_sim[0])

    start = default_timer()
    for i in range(1,N_inner):
        ## Update a
        a_tilde = propose(a_sim[i-1], a_values)
        theta_tilde = prob(d_given, a_tilde)

        num = a_util(a_tilde, theta_tilde)
        den = a_util(a_sim[i-1], theta_sim)

        if np.random.uniform() <= num/den:
            a_sim[i] = a_tilde
            theta_sim = theta_tilde
        else:
            a_sim[i] = a_sim[i-1]

        if i > burnin*N_inner:
            a_dist = a_sim[int(burnin*N_inner):i]
            a_opt = mode(a_dist)[0][0]
            ##
            if math.isclose(a_opt, a_optimal):
                break
    end = default_timer()
    ##
    print('Elapsed APS time: ', end-start)
    ##
    #a_opt = mode(a_dist)[0][0]
    print('Optimal APS attack for given defense', a_opt)

################################################################################
## APS for attacker, continuous case
################################################################################
if case == "continuous":
    d_given = 0.9
    N_inner = 100000
    prec = 0.001
    #
    a_sim = np.zeros(N_inner, dtype = float)
    a_sim[0] = np.random.uniform(0,1)
    theta_sim = prob(d_given, a_sim[0])
    ##
    # def beta_params(mu, var):
    #     alpha = ( (1-mu)/var - 1/mu ) * mu**2
    #     beta = ( 1/mu - 1 )*alpha
    #     return alpha, beta
    #
    # def propose(mu, var):
    #     a, b = beta_params(mu, var)
    #     prop = np.random.beta(a, b)
    #     return prop
    def propose():
        return( np.random.uniform(0,1) )

    # var = 0.001
    start = default_timer()
    for i in range(1,N_inner):
        ## Update a
        a_tilde = propose()#propose(a_sim[i-1], var)
        theta_tilde = prob(d_given, a_tilde)

        num = a_util(a_tilde, theta_tilde)
        den = a_util(a_sim[i-1], theta_sim)

        if np.random.uniform() <= num/den:
            a_sim[i] = a_tilde
            theta_sim = theta_tilde
        else:
            a_sim[i] = a_sim[i-1]
    end = default_timer()
    print('Elapsed APS time: ', end-start)
    ##
    burnin = 0.5
    a_dist = a_sim[int(burnin*N_inner):]
    # a_opt = mode(a_dist)[0][0]
    #a_dist = np.array([1,1,2,2,3,4,5,3.5])
    count, bins = np.histogram(a_dist, bins = int(1.0/prec) )
    a_opt = ( bins[count.argmax()] + bins[count.argmax()+1] ) / 2
    #a_opt = mode(a_dist)[0][0]
    print('Optimal APS attack for given defense', a_opt)
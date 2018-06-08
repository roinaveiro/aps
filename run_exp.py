#!/usr/bin/env python
import sys
import argparse
import numpy as np
import pandas as pd
from timeit import default_timer
from importlib import import_module
from contextlib import contextmanager

sys.path.append('.')
from mcmc import mcmc_atk_def, mcmc_ara
from aps import aps_atk_def, aps_ara

@contextmanager
def timer():
    start = default_timer()
    try:
        yield
    finally:
        end = default_timer()
        print("Elapsed time (s): {:.6f}".format(end - start))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p',
                dest='module',
                help='module with problem specific information',
                default='prob1',
                choices=['prob1', 'prob2', 'prob1_v2'])

    parser.add_argument('-a',
                dest='alg',
                help='algorithm',
                default='mcmc',
                choices=['mcmc', 'aps'])

    parser.add_argument('-s',
                dest='set',
                help='setting',
                default='atk_def',
                choices=['atk_def', 'ara'])

    parser.add_argument('-o',
                dest='output',
                help='output dir',
                default='.')

    parser.add_argument('--njobs',
                type=int,
                dest='njobs',
                help='Number of jobs',
                default=1)

    parser.add_argument('--mcmc',
                type=int,
                dest='mcmc',
                help='Number of MCMC iterations',
                default=10000)

    parser.add_argument('--ara',
                type=int,
                dest='ara',
                help='Number of ARA iterations',
                default=1000)

    parser.add_argument('--prob',
                dest='prob',
                help='Probability density p(a | d)',
                default=None)

    parser.add_argument('--aps',
                type=int,
                dest='aps',
                help='Number of outer APS iterations',
                default=10000)

    parser.add_argument('--aps_inner',
                type=int,
                dest='aps_inner',
                help='Number of inner APS iterations',
                default=1000)

    parser.add_argument('--burnin',
                type=float,
                dest='burnin',
                help='Percentage of iterations to discard',
                default=0.75)

    args = parser.parse_args()

    p = import_module(args.module)

    np.random.seed(1234)

    d_idx = pd.Index(p.d_values, name='d')
    a_idx = pd.Index(p.a_values, name='a')

    #---------------------------------------------------------------------------
    # Attacker-defender game
    #---------------------------------------------------------------------------
    if args.set == 'atk_def':
        print('Game theory')
        print('-' * 80)

        if args.alg == 'mcmc':
            print('MCMC')
            with timer():
                d_opt, a_opt, psi_d, psi_a = mcmc_atk_def(p.d_values, p.a_values,
                                                          p.d_util, p.a_util,
                                                          p.prob, p.prob,
                                                          mcmc_iters=args.mcmc)
        elif args.alg == 'aps':
            print('APS')
            with timer():
                d_opt, a_opt, psi_d, psi_a = aps_atk_def(p.d_values, p.a_values,
                                                         p.d_util, p.a_util,
                                                         p.prob, N_aps=args.aps,
                                                         burnin=args.burnin,
                                                         N_inner=args.aps_inner)
        else:
            print('Error')

        a_opt = pd.Series(a_opt, index=d_idx)
        psi_d = pd.Series(psi_d, index=a_idx)
        psi_a = pd.DataFrame(psi_a, index=d_idx, columns=a_idx)
        dout = {'d_opt': d_opt, 'a_opt': a_opt, 'psi_d': psi_d, 'psi_a': psi_a}
    #---------------------------------------------------------------------------
    # ARA
    #---------------------------------------------------------------------------
    elif args.set == 'ara':
        print('\nARA')
        print('-' * 80)

        if args.prob:
            p_d = pd.read_pickle('{}'.format(args.prob)).values
            print(p_d)
        else:
            p_d = None

        if args.alg == 'mcmc':
            print('MCMC')
            with timer():
                d_opt, p_a, psi_d, psi_a = mcmc_ara(p.d_values, p.a_values,
                                                    p.d_util, p.a_util_f, p.prob,
                                                    p.a_prob_f,
                                                    mcmc_iters=args.mcmc,
                                                    ara_iters=args.ara,
                                                    n_jobs=args.njobs)

        elif args.alg == 'aps':
            print('APS')
            with timer():
                d_opt, p_a, psi_da, psi_ad = aps_ara(p.d_values, p.a_values,
                                                   p.d_util, p.a_util_f, p.prob,
                                                   p.a_prob_f, N_aps=args.aps,
                                                   J=args.ara,
                                                   burnin=args.burnin, p_d=p_d,
                                                   N_inner=args.aps_inner)
        else:
            print('Error')

        a_opt = pd.Series(p_d.argmax(axis=1), index=d_idx)
        psi_d = pd.Series(psi_da.sum(axis=1), index=a_idx)
        psi_a = pd.DataFrame(psi_ad.mean(axis=2), index=d_idx, columns=a_idx)
        p_a = pd.DataFrame(p_a, index=d_idx, columns=a_idx)
        dout = {'d_opt': d_opt, 'a_opt': a_opt, 'psi_d': psi_d, 'psi_a': psi_a,
                'psi_da': psi_da, 'psi_ad': psi_ad, 'p_a': p_a}
        with pd.option_context('display.max_columns', len(p.a_values)):
            print(p_a)
    else:
        print('Error')

    print(d_opt)
    print(a_opt)
    print(psi_d)
    with pd.option_context('display.max_columns', len(p.a_values)):
        print(psi_a)

    fout = '{}/{}_{}_{}.pkl'.format(args.output, args.module, args.set, args.alg)
    with open(fout, "wb") as f:
        pickle.dump(dout, f)

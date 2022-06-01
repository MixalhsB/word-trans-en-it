"""Word translation

Usage:
  plsr_regression.py --ncomps=<n> --nns=<n> [-v | --verbose]
  plsr_regression.py (-h | --help)
  plsr_regression.py --version

Options:
  --ncomps=<n>   Number of principal components; or "0" in order to run hyperparameter search
  --nns=<n>      Number of nearest neighbours for the evaluation
  -h --help      Show this screen.
  --version      Show version.
  -v --verbose   Show verbose output.

"""

from docopt import docopt
from matplotlib import pyplot as plt
from sklearn.cross_decomposition import PLSRegression
import json
import utils
import warnings
import numpy as np
import seaborn as sns


def mk_training_matrices(pairs, en_dimension, it_dimension, english_space, italian_space):
    en_mat = np.zeros((len(pairs), en_dimension)) 
    it_mat = np.zeros((len(pairs), it_dimension))
    c = 0
    for p in pairs:
        en_word,it_word = p.split()
        en_mat[c] = english_space[en_word]   
        it_mat[c] = italian_space[it_word]   
        c += 1
    return en_mat,it_mat


def PLSR(mat_english, mat_italian, ncomps):
    plsr = PLSRegression(n_components=ncomps)
    plsr.fit(mat_english, mat_italian)
    return plsr


def run_cross_validation(ncomps, nns, verbose, english_space, italian_space, all_pairs):   
    np.random.seed(0)
    np.random.shuffle(all_pairs)
    min_test_size = len(all_pairs) // 5
    add = [1 for _ in range(len(all_pairs) - min_test_size * 5)]
    add += [0 for _ in range(5 - len(add))]
    shift = 0
    precisions = []
    for round in range(5):
        test_size = min_test_size + add[round]
        test_pairs = all_pairs[shift : shift + test_size]
        training_pairs = all_pairs[: shift] + all_pairs[shift + test_size :]
        shift += test_size
        en_mat, it_mat = mk_training_matrices(training_pairs, 300, 300, english_space, italian_space)
        plsr = PLSR(en_mat, it_mat, ncomps)
        print('-> cross-validation round', round + 1, '/', 5)
        score = 0
        for p in test_pairs:
            en, it = p.split()
            predicted_vector = plsr.predict(english_space[en].reshape(1, -1))[0]
            nearest_neighbours = utils.neighbours(italian_space, predicted_vector, nns)
            if it in nearest_neighbours:
                score += 1
                if verbose:
                    print(en, it, nearest_neighbours, '1')
            else:
                if verbose:
                    print(en, it, nearest_neighbours, '0')
        precisions.append(score / len(test_pairs))
    return np.mean(precisions)


def main():
    '''Verify given arguments'''
    warnings.filterwarnings('ignore')
    args = docopt(__doc__, version='PLSR regression for word translation 1.1')
    ncomps = int(args['--ncomps'])
    nns = int(args['--nns'])
    verbose = False
    if args['--verbose']:
        verbose = True
    assert ncomps >= 0 and nns >= 1
    
    '''Read semantic spaces'''
    english_space = utils.readDM('data/english.subset.388.dm')
    italian_space = utils.readDM('data/italian.subset.388.dm')
    
    '''Read all word pairs'''
    all_pairs = []
    f = open('data/pairs_en_it.txt')
    for l in f:
        l = l.rstrip('\n')
        all_pairs.append(l)
    f.close()
    
    '''Initiate PLSR cross-validation'''
    if ncomps:
        avg_precision = run_cross_validation(ncomps, nns, verbose, english_space, italian_space, all_pairs)
        print('Avg. precision PLSR:', avg_precision)
        return {(ncomps, nns): avg_precision}
    else: # run hyper-parameter search
        X, Y = [x for x, _ in stored_avg_precisions], [y for y in stored_avg_precisions.values()]
        _ = sns.lineplot(x='Number of components', y='Precision @ 5',
                         data={'Number of components': X, 'Precision @ 5': Y})
        data_output_filename = 'ncomps-precision-values_nns=' + str(nns) + '.json'
        with open(data_output_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps({str((ncomps, nns)) : stored_avg_precisions[ncomps, nns] for ncomps, nns in stored_avg_precisions},
                    indent = 4, ensure_ascii=False))
        print('Saved precision values to ./' + data_output_filename)
        fig_output_filename = 'ncomps-precision-plot_nns=' + str(nns) + '.pdf'
        plt.savefig(fig_output_filename, bbox_inches='tight')
        print('Saved summarising plot to ./' + fig_output_filename)
        return stored_avg_precisions


if __name__ == '__main__':
    result_dict = main()

# coding: utf-8
import math
import re
import pymorphy2
import web

import config
from models.word_lists import excluded_words

DB = config.DB


class Classifier:
    def __init__(self):
        # Счетчики комбинаций признак/категория
        self.fc = {}
        # Счетчики документов в каждой категории
        self.cc = {}

    # Увеличить счетчик пар признак/категория
    def inc_f(self, f, cat, user_id):
        count = self.f_count(f, cat, user_id)
        if count == 0:
            DB.insert(
                'fc',
                user_id=user_id,
                feature=f,
                category=cat,
                cnt=1
            )
        else:
            DB.update(
                'fc',
                where="feature=$feature AND category=$category AND user_id=$user_id",
                vars={'feature': f, 'category': cat, 'user_id': user_id},
                cnt=web.db.SQLLiteral('cnt+1')
            )

    # Увеличить счетчик применений категории
    def inc_c(self, cat, user_id):
        count = self.cat_count(cat, user_id)
        if count == 0:
            DB.insert(
                'cc',
                user_id=user_id,
                category=cat,
                cnt=1
            )
        else:
            DB.update(
                'cc',
                where="category=$category AND user_id=$user_id",
                vars={'category': cat, 'user_id': user_id},
                cnt=web.db.SQLLiteral('cnt+1')
            )

    # Сколько раз признак появлялся в данной категории
    def f_count(self, f, cat, user_id):
        res = DB.select(
            'fc',
            where="feature=$feature AND category=$category AND user_id=$user_id",
            vars={'feature': f, 'category': cat, 'user_id': user_id}
        )
        if not res:
            return 0
        else:
            return float(res[0]['cnt'])

    # Сколько образцов отнесено к данной категории
    def cat_count(self, cat, user_id):
        res = DB.select(
            'cc',
            where="category=$category AND user_id=$user_id",
            vars={'category': cat, 'user_id': user_id},
            limit=1
        )
        if not res:
            return 0
        else:
            return float(res[0]['cnt'])

    # Общее число образцов
    def total_count(self, user_id):
        res = DB.query("SELECT SUM(cnt) sum_cnt FROM cc WHERE user_id=$user_id", vars={'user_id': user_id})
        if not res:
            return 0
        return res[0]['sum_cnt']

    # Список всех категорий
    def categories(self, user_id):
        res = DB.query("SELECT category FROM cc WHERE user_id=$user_id", vars={'user_id': user_id})
        return [row['category'] for row in res]

    def f_prob(self, f, cat, user_id):
        if self.cat_count(cat, user_id) == 0:
            return 0
        # Общее число раз, когда данный признак появлялся в этой категории,
        # делим на количество образцов в той же категории
        return self.f_count(f, cat, user_id) / self.cat_count(cat, user_id)

    def weighted_prob(self, f, cat, user_id, prf, weight=1.0, ap=0.5):
        # Вычислить текущую вероятность
        basicprob = prf(f, cat, user_id)
        # Сколько раз этот признак встречался во всех категориях
        totals = sum([self.f_count(f, c, user_id) for c in self.categories(user_id)])
        # Вычислить средневзвешенное значение
        bp = ((weight * ap) + (totals * basicprob)) / (weight + totals)
        return bp

    def train(self, features, cat, user_id):
        # Увеличить счетчики для каждого признака в данной классификации
        for f in features:
            self.inc_f(f, cat, user_id)
        # Увеличить счетчик применений этой классификации
        self.inc_c(cat, user_id)
        # add commit


class FisherClassifier(Classifier):
    def __init__(self):
        Classifier.__init__(self)
        self.minimums = {}

    def cprob(self, f, cat, user_id):
        # The frequency of this feature in this category
        clf = self.f_prob(f, cat, user_id)
        if clf == 0:
            return 0

        # The frequency of this feature in all the categories
        freqsum = sum([self.f_prob(f, c, user_id) for c in self.categories(user_id)])

        # The probability is the frequency in this category divided by
        # the overall frequency
        p = clf / freqsum
        return p

    def fisherprob(self, features, cat, user_id):
        # Multiply all the probabilities together
        p = 1
        for f in features:
            p *= (self.weighted_prob(f, cat, user_id, self.cprob))

        # Take the natural log and multiply by -2
        fscore = -2 * math.log(p)

        # Use the inverse chi2 function to get a probability
        return self.invchi2(fscore, len(features) * 2)

    def invchi2(self, chi, df):
        m = chi / 2.0
        sum = term = math.exp(-m)
        for i in range(1, df // 2):
            term *= m / i
            sum += term
        return min(sum, 1.0)

    def setminimum(self, cat, min):
        self.minimums[cat] = min

    def getminimum(self, cat):
        if cat not in self.minimums:
            return 0
        return self.minimums[cat]

    def classify(self, features, user_id, default=None):
        # Loop through looking for the best result
        best = default
        max_prob = 0.0
        res = {'cat': None, 'good': 0, 'bad': 0}
        for c in self.categories(user_id):
            p = self.fisherprob(features, c, user_id)
            # Make sure it exceeds its minimum
            if p > self.getminimum(c) and p > max_prob:
                best = c
                max_prob = p
            res[c] = p
        res['cat'] = best
        print res
        return res

    def get_rating(self, features, user_id, default=None):
        res = self.classify(features, user_id, default)
        rating = res['good'] - res['bad']
        rating = int(round(rating, 2) * 100)
        return rating


class FeatureParser:
    def print_word_array(self, words):
        print '----------------------------------------'
        for word in words:
            print u"'{0}-{1}',".format(word, len(word)),
        print ''
        print '----------------------------------------'

    def _is_good_words(self, word):
        if word in excluded_words:
            return False
        if len(word) < 5 or len(word) > 13:
            return False

        return True

    def _is_contains_number(self, word):
        num = re.compile('.*\\d+.*')
        if num.match(word):
            return True

    def _get_words(self, txt):
        # Split the words by non-alpha characters
        splitter = re.compile('\\W*', re.UNICODE)
        words = []
        ma = pymorphy2.MorphAnalyzer()
        arr = set(splitter.split(txt))
        for w in arr:
            w = w.lower().replace('_', '')
            if not self._is_good_words(w) or self._is_contains_number(w):
                continue

            res = ma.parse(w)
            if res:
                w = res[0].normal_form
                if self._is_good_words(w):
                    words.append(w)

        # Return the unique set of words only
        result = sorted(set(words))
        #self.print_word_array(result)
        return result

    def get_features(self, article):
        return self._get_words(article.description)

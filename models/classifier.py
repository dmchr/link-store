# coding: utf-8
import config
import math
import web

DB = config.DB


class Classifier:
    def __init__(self, get_features_fnc):
        # Счетчики комбинаций признак/категория
        self.fc = {}
        # Счетчики документов в каждой категории
        self.cc = {}
        self.get_features = get_features_fnc

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

    def train(self, item, cat, user_id):
        features = self.get_features(item)
        # Увеличить счетчики для каждого признака в данной классификации
        for f in features:
            self.inc_f(f, cat, user_id)
        # Увеличить счетчик применений этой классификации
        self.inc_c(cat, user_id)
        # add commit


class FisherClassifier(Classifier):
    def __init__(self, getfeatures):
        Classifier.__init__(self, getfeatures)
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

    def fisherprob(self, item, cat, user_id):
        # Multiply all the probabilities together
        p = 1
        features = self.get_features(item)
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

    def classify(self, item, user_id, default=None):
        # Loop through looking for the best result
        best = default
        max_prob = 0.0
        for c in self.categories(user_id):
            p = self.fisherprob(item, c, user_id)
            # Make sure it exceeds its minimum
            if p > self.getminimum(c) and p > max_prob:
                best = c
                max_prob = p
            print c, p
        return best

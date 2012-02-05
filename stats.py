#!/usr/bin/python
# -*- coding: utf-8 -*-

import re,os,sys
import nltk
import fnmatch
import codecs
import random
from collections import Counter, defaultdict
from nltk.probability import FreqDist, ConditionalFreqDist
from nltk.classify import NaiveBayesClassifier
from nltk.tokenize import sent_tokenize, wordpunct_tokenize, word_tokenize
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import movie_reviews, stopwords
from nltk.corpus import words as eng

def replace(text):
    rp = [ 
      (ur"won['’]t", 'will not'),
      (ur"\(.\)", ''),
      (ur"can['’]t", 'cannot'),
      (ur"i['’]m", 'i am'),
      (ur"ain['’]t", 'is not'),
      (ur"a.m.", 'am'),
      (ur"p.m.", 'pm'),
      (ur"(\w+)['’]ll", '\g<1> will'),
      (ur"(\w+)n['’]t", '\g<1> not'),
      (ur"(\w+)['’]ve", '\g<1> have'),
      (ur"(\w+)['’]s", '\g<1> is'),
      (ur"(\w+)['’]re", '\g<1> are'),
      (ur"(\w+)['’]d", '\g<1> would')
    ]   
    patterns = [(re.compile(regex), repl) for (regex, repl) in rp]
    s = text
    for (pattern, repl) in patterns:
        (s, count) = re.subn(pattern, repl, s)
    return s


def evaluate_classifier(featx):
    negids = movie_reviews.fileids('neg')
    posids = movie_reviews.fileids('pos')
    negfeats = [(featx(movie_reviews.words(fileids=[f])), 'neg') for f in negids]
    posfeats = [(featx(movie_reviews.words(fileids=[f])), 'pos') for f in posids]
 
    negcutoff = len(negfeats)*3/4
    poscutoff = len(posfeats)*3/4
 
    trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
    testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
    classifier = NaiveBayesClassifier.train(trainfeats)
    return classifier

def best_word_feats(words):
    return dict([(word, True) for word in words if word in bestwords])


eng_all = codecs.open('wordlist.txt','r','utf8')
ws = set([w.rstrip().lower() for w in eng_all.readlines()])
eng_all.close()
sw = set(stopwords.words('english'))
word_data = defaultdict(Counter)
data = defaultdict(Counter)
s_data = defaultdict(list)


print "initializing classifier (this takes awhile)"
word_fd = FreqDist()
label_word_fd = ConditionalFreqDist()
for word in movie_reviews.words(categories=['pos']):
    word_fd.inc(word.lower())
    label_word_fd['pos'].inc(word.lower())
for word in movie_reviews.words(categories=['neg']):
    word_fd.inc(word.lower())
    label_word_fd['neg'].inc(word.lower())
 
pos_word_count = label_word_fd['pos'].N()
neg_word_count = label_word_fd['neg'].N()
total_word_count = pos_word_count + neg_word_count
 
word_scores = {}
for word, freq in word_fd.iteritems():
    pos_score = BigramAssocMeasures.chi_sq(label_word_fd['pos'][word],
        (freq, pos_word_count), total_word_count)
    neg_score = BigramAssocMeasures.chi_sq(label_word_fd['neg'][word],
        (freq, neg_word_count), total_word_count)
    word_scores[word] = pos_score + neg_score
 
best = sorted(word_scores.iteritems(), key=lambda (w,s): s, reverse=True)[:10000]
bestwords = set([w for w, s in best])
c = evaluate_classifier(best_word_feats)
classify = lambda x: c.classify(best_word_feats(x))
print "done with init classifiy"

for root, dirnames, filenames in os.walk('by_name/'):
    for name in filenames:
        label = "other"
        if re.match('JUSTICE.*',name ):
            label = name 
            print label
        fp = codecs.open('by_name/' + name,'r','utf8' )
        for l in fp.readlines():
            # one line = one statement
            # expand contractions
            l = replace(l.lower())
            # throw everything to the sentiment tester
            statement = False
            c_data = Counter()
            for s in sent_tokenize(l):
                # tokenize
                words = [word for word in wordpunct_tokenize(s)]
                # remove words that aren't in the dictionary
                words=filter(lambda x: x in ws, words)
                if len(words) == 0:
                    # no real words in this sentence
                    continue
                for w in words:
                    c_data[w] += 1
                    word_data[label][w] +=1
                c_data['_num_sentences'] += 1
                data[label]['_num_sentences'] += 1
                statement = True 
            if statement: 
                c_data['_' + classify(wordpunct_tokenize(l))] += 1
                s_data[label].append(c_data)
                data[label]['_' + classify(wordpunct_tokenize(l))] += 1
                data[label]['_num_statements'] += 1


print "All Data\n---------------------------\n"
print r'<tr><th></th><th>statements</th><th>sentences</th><th>words</th><th>stopwords</th><th>unique words</th></tr>'

for label in ['JUSTICE_ROBERTS', 'JUSTICE_ALITO', 'JUSTICE_SCALIA', 'JUSTICE_THOMAS', 'JUSTICE_KENNEDY', 'JUSTICE_BREYER', 'JUSTICE_GINSBURG', 'JUSTICE_KAGAN', 'JUSTICE_SOTOMAYOR', 'other']:
    words = Counter(dict([(word,cnt) for word,cnt in word_data[label].items() if word not in sw and re.match('[^_]',word)]))
    stopwords = Counter(dict([(word,cnt) for word,cnt in word_data[label].items() if word in sw and re.match('[^_]',word)]))
    max_l=len(max(words.keys(), key=lambda x: len(x)))
    min_l=len(min(words.keys(), key=lambda x: len(x)))
    chart_data = [] 
    chart_data.extend([label,str(data[label]['_num_statements']),str(data[label]['_num_sentences']),str(sum(words.values())),str(sum(stopwords.values())),str(len(words.keys()))])

    print '<tr><td>' + '</td><td>'.join(chart_data) + '</td></tr>'


print "50 Random Samples\n---------------------------\n"
print r'<tr><th></th><th>sentences</th><th>words</th><th>stopwords</th><th>unique words</th></tr>'

for label in ['JUSTICE_ROBERTS', 'JUSTICE_ALITO', 'JUSTICE_SCALIA', 'JUSTICE_KENNEDY', 'JUSTICE_BREYER', 'JUSTICE_GINSBURG', 'JUSTICE_KAGAN', 'JUSTICE_SOTOMAYOR', 'other']:
    try:
        r_cntlist = random.sample(s_data[label],500)
    except ValueError:
        print "not enough data for " + label
        continue
    cnt_sum = Counter()
    for cnt in r_cntlist: 
        cnt_sum += cnt
    words = Counter(dict([(word,cnt) for word,cnt in cnt_sum.items() if word not in sw and re.match('[^_]',word)]))
    stopwords = Counter(dict([(word,cnt) for word,cnt in cnt_sum.items() if word in sw and re.match('[^_]',word)]))
    chart_data = [] 
    num_w = sum(words.values())
    num_s = cnt_sum['_num_sentences']
    unique_w = len(words.keys())
    chart_data.extend([label,str(num_s),str(num_w),str(sum(stopwords.values())),str(unique_w)])
    print '<tr><td>' + '</td><td>'.join(chart_data) + '</td></tr>',
    print round(float(num_w)/float(num_s), 2),
    print round(float(unique_w)/float(num_w), 2)
    for w in words.most_common(10):
                print "         " + str(w)
    print "positive: " + str(cnt_sum['_pos'])
    print "negative: " + str(cnt_sum['_neg'])


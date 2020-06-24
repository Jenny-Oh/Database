#import pyfpgrowth
from konlpy.tag import Mecab
from pymongo import MongoClient
from bson.objectid import ObjectId
#import fpgrowth
stop_word = dict()
DBname = "db20181657"
conn = MongoClient('localhost')
db = conn[DBname]
db.authenticate(DBname, DBname)

class Node:
    def __init__(self,key,item):
        self.item=item
        self.key = key
        self.left=None
        self.right=None

class Tree:
    def __init__(self):
        self.head = None

    def inorder(self):
        traversal=[]
        if self.left: traversal+= self.left.inorder()
        traversal.append(self.data)
        if self.right: traversal+= self.right.inorder()
        return traversal
    def inc(self, sup):
        self.support += sup
    """
    def insert(self,key,item):
        if self.head == None:
            self.head = Node(0,'root')
        else:
            self.current_node = self.head
            while True:
                if self.current_node.left == None:
                    self.current_node.left = Node(key,item)
                elif self.current_node.left.item == item:
                    self.current_node.left.support = self.current_node.left.support + 1
                else:
                    self.current_node.right = Node(key,item)

        if not self.left: self.left = Node(key,item)
        else: self.right = self.right=Node(key,item)
    """
def make_stop_word():
    f = open("wordList.txt","r")
    while True:
        line = f.readline()
        if not line:
            break
        stop_word[line.strip()] = True
    f.close()

def morphing(content):
    mecab = Mecab()
    morphList = []
    for word in mecab.nouns(content):
        if word not in stop_word:
            morphList.append(word)
    return morphList

def p0():
    col1 = db['news']
    col2 = db['news_freq']

    col2.drop()

    for doc in col1.find():
        contentDic = dict()
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col2.insert(contentDic)

def p1():
    for doc in db['news_freq'].find():
        doc['morph'] = morphing(doc['content'])
        db['news_freq'].update({"_id": doc['_id']}, doc)
def p2():
    #all news articles are morphing and updated
    for doc in db['news'].find():
      doc['morph']=morphing(doc['content'])
      db['news'].update({"_id": doc['_id']},doc)

    #randomly choose one article
    article = db['news'].aggregate([{'$sample':{'size':1}}])
    for doc in article:
        for item in doc['morph']:
            print(item)
    pass
def p3():
    col1 = db['news_freq']
    col2 = db['news_wordset']
    col2.drop()
    for doc in col1.find():
        new_doc = dict()
        new_set = set()
        for w in doc['morph']:
            new_set.add(w)
        new_doc['word_set'] = list(new_set)
        new_doc['news_freq_id'] = doc['_id']
        col2.insert(new_doc)

def p4():
    """
    TODO:
    output: news wordset of db.news_wordset.findOne()
    """
    wordset = db['news_wordset'].aggregate([{'$sample' : {'size': 1}}])
    for doc in wordset:
        for item in doc['word_set']:
            print(item)
    pass
def p5(length):
    """
    TODO:
    make frequent item_set
    and insert new collection (candidate_L+"length")
    ex) 1-th 
    """
     
    # frequent itemset : dictionary type
    freq_item = dict()
    
    # freq itemset DB
    col1 = db['candidate_L1']
    col2 = db['candidate_L2']
    col3 = db['candidate_L3']
    col1.drop()
    col2.drop()
    col3.drop()

    #make word set
    transaction = []
    wordset = set()
    for doc in db['news_wordset'].find():
        for item in doc['word_set']:
            wordset.add(item)
        transaction.append(doc['word_set'])
    # calculate "support"
    for item in wordset:
        support = 0
        for doc2 in db['news'].find():
            if item in doc2['content']:
                support = support + 1
        if support > 24:
            freq_item['item_set'] = item
            freq_item['support'] = support
            freq_item['_id'] = ObjectId()
            col1.insert(freq_item)
    
    fptable=[]
    # build db['candidate_L1']  
    for doc in db['news_wordset'].find():
        for item in doc['word_set']:
            word = dict()
            w_list = list()
            sup = db['candidate_L1'].find({'$project':{"_id":0, "item_set":0, "support" :1}},{"item_set": item})
            word['item'] = item
            word['support'] = sup
            w_list.append(word)
            #print(type(w_list))
        new = sorted(w_list, key =(lambda x: x['support']))
        fptable.append(new)
    if length == 1:
        for doc in db['candidate_L1'].find():
            print(doc)
        return

    #print('L1 finish\n')
    # find min_sup
    min_sup = 600
    min_item = []
    for doc in db['candidate_L1'].find():
        if doc['support'] < min_sup:
            min_sup = doc['support']
            min_item = doc['item_set']
    #print('min_sup %d\n'%min_sup)        
    
    # FP-growth tree
    
    root = Tree()
    
    tmp = root
    # 1st list just insert
    for d in range(len(fptable[0])):
        tmp = root
        item = fptable[0][d]['item'] 
        sup = fptable[0][d]['support']
        if root.head== None:
            root = Node(0,'root')
            root.left=Node(sup,item)
        else:
            while True:
                if tmp.left == None:
                    tmp.left = Node(sup,item)
                else:
                    tmp = tmp.left
    print(root.item)
    # else tree
    for i in range(1, len(fptable)):
        tmp = root
        for j in range(len(fptable[i])):
            item = fptable[i][j]['item']
            sup = fptable[i][j]['support']
            if tmp.left == None:
                tmp.left = Node(sup,item)
                tmp = tmp.left
                continue
            elif tmp.left == item:
                tmp = tmp.left
                tmp.key = tmp.key + 1
                continue
            elif tmp.right == None:
                tmp.right = Node(sup,item)
                tmp = tmp.right
                continue
            elif tmp.right == item:
                tmp = tmp.right
                tmp.key =tmp.key + 1

    #print('finish Tree!\n')
    
    #root.search(min_sup,item)
    """
    freq2 = dict()
    freq3 = dict()
    patterns = pyfpgrowth.find_frequent_patterns(transactions,24) 
    if length == 2:
        for item in patterns:
            if len(item) == 2:
                freq2['item'] = item
                freq2['support'] = patterns[item]
                freq2['_id'] = ObjectId()
                col2.insert(freq2)
    elif length == 3:
        for item in patterns:
            if len(item) == 3:
                freq3['item'] = item
                freq3['support']=patterns[item]
                freq3['_id'] = ObjectId()
                col3.insert(freq3)
    print('finish freq_itemset!\n')
    
    if length == 2:
        for doc in db['candidate_L2']:
            print(doc)
    elif length == 3:
        for doc in db['candidate_L3']:
        print(doc)
    """
    pass

def p6(length):
    #rules =pyfpgrowth.generate_association_rules(patterns,0.6)
    col2 = db['candidate_L2']
    col3 = db['candidate_L3']
    itemset = []
    if length == 2:
        for doc in col2:
            itemset.insert({doc['item']:doc['support']})
    elif length == 3:
        for doc in col3:
            itemset.insert({doc['item']:doc['suppport']})
    #rules = pyfpgrowth.generate_association_rules(itemset,0.6)
    #for item in rules:
    #    print(item)
    pass
    

def printMenu():
    print("0. CopyData")
    print("1. Morph")
    print("2. print morphs")
    print("3. print wordset")
    print("4. frequent item set")
    print("5. association rule")

if __name__ == "__main__":
    make_stop_word()
    printMenu()
    selector = int(input())
    if selector == 0:
        p0()
    elif selector == 1:
        p1()
        p3()
    elif selector == 2:
        p2()
    elif selector == 3:
        p4()
    elif selector == 4:
        print("input length of the frequent item:")
        length = int(input())
        p5(length)
    elif selector == 5:
        print("input length of the frequent item:")
        length = int(input())
        #p6(length)

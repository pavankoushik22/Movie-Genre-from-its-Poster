# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in 

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import glob
import scipy.misc
import tensorflow as tf
# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list the files in the input directory
import scipy
import os
print(os.listdir("../input"))
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
# Any results you write to the current directory are saved as output.
image_paths = glob.glob("../input/samplemovieposters/SampleMoviePosters/*.jpg")
image_ids = []
for path in image_paths:
    start = path.rfind("/")+1
    end = len(path)-4
    image_ids.append(path[start:end])
data = pd.read_csv("../input/MovieGenre.csv", encoding = "ISO-8859-1")
y = []
classes = tuple()
for image_id in image_ids:
    genres = tuple((data[data["imdbId"] == int(image_id)]["Genre"].values[0]).split("|"))
    y.append(genres)
    classes = classes + genres
mlb = MultiLabelBinarizer()
mlb.fit(y)
y = mlb.transform(y)
classes = set(classes)

def get_image(image_path):
    image = scipy.misc.imread(image_path)
    image = scipy.misc.imresize(image, (150, 150))
    image = image.astype(np.float32)
    return image
x = []
for path in image_paths:
    x.append(get_image(path))
x = np.asarray(x)
trainx, testx, trainy, testy = train_test_split(x,y,test_size = 0.05, random_state = 42)

def random_minibatches(x,y,size=64, seed = 0):
    #x = tf.shuffle(x, seed)
    #y = tf.shuffle(y, seed)
    m = x.shape[0]
    nums = m//size
    batches = []
    for k in range(nums):
        mx = x[k*size:(k+1)*size,:,:,:]
        my = y[k*size:(k+1)*size,:]
        batches.append((mx,my))
    mx = x[nums*size:m,:,:,:]
    my = y[nums*size:m,:]
    batches.append((mx,my))
    return batches


def create_placeholders(nh0, nw0, nc0, ny):
    x = tf.placeholder("float", shape = (None, nh0, nw0, nc0))
    y = tf.placeholder("float", shape = (None, ny))
    return x,y

def init_weights():
    w1 = tf.get_variable("w1",[3,3,3,128], initializer = tf.contrib.layers.xavier_initializer_conv2d(seed = 2))
    w2 = tf.get_variable("w2",[3,3,128,64], initializer = tf.contrib.layers.xavier_initializer_conv2d(seed = 2))
    w3 = tf.get_variable("w3",[2,2,64,64], initializer = tf.contrib.layers.xavier_initializer_conv2d(seed = 2))
    w4 = tf.get_variable("w4",[2,2,64,32], initializer = tf.contrib.layers.xavier_initializer_conv2d(seed = 2))
    params = {"w1":w1,"w2":w2,"w3":w3,"w4":w4}
    return params


def forward_prop(x, params):
    w1 = params["w1"]
    w2 = params["w2"]
    w3 = params["w3"]
    w4 = params["w4"]
    z1 = tf.nn.conv2d(x,w1,[1,1,1,1],padding = 'SAME')
    a1 = tf.nn.relu(z1)
    dp1 = tf.nn.dropout(a1, 0.7)
        
    z2 = tf.nn.conv2d(dp1,w2,[1,1,1,1], padding = 'SAME')
    a2 = tf.nn.relu(z2)
    p2 = tf.nn.max_pool(a2, ksize = [1,3,3,1], strides = [1,1,1,1], padding = 'SAME')
    dp2 = tf.nn.dropout(p2, 0.7)
    
    z3 = tf.nn.conv2d(dp2, w3, [1,1,1,1],padding = 'SAME')
    a3 = tf.nn.relu(z3)
    p3 = tf.nn.max_pool(a3, ksize = [1,2,2,1], strides = [1,1,1,1], padding = 'SAME')
    dp3 = tf.nn.dropout(p3, 0.8)
    
    z4 = tf.nn.conv2d(dp3, w4, [1,1,1,1],padding = 'SAME')
    a4 = tf.nn.relu(z4)
    dp4 = tf.nn.dropout(a4, 0.8)
    
    fc1 = tf.contrib.layers.flatten(dp4)
    fc2 = tf.contrib.layers.fully_connected(fc1, num_outputs = 46, activation_fn = tf.nn.relu)
    fc3 = tf.contrib.layers.fully_connected(fc2, num_outputs = 23, activation_fn = None)
    return fc3


def loss(fc3, y):
    cost = tf.nn.sigmoid_cross_entropy_with_logits(logits = fc3, labels = y)
    cost = tf.reduce_mean(cost)
    return cost


def model(trainx, trainy, testx, testy, learning_rate = 0.009, epochs = 30):
    (m, nh0, nw0, nc0) = trainx.shape
    (m, ny) = trainy.shape
    x, y = create_placeholders(nh0, nw0, nc0, ny)
    costs = []
    params = init_weights()
    fc3 = forward_prop(x,params)
    cost = loss(fc3, y)
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
    init = tf.global_variables_initializer()
    nums = m//64
    with tf.Session() as sess:
        sess.run(init)
        for i in range(epochs):
            minibatches = random_minibatches(trainx, trainy, size = 64)
            lcost = 0
            cnt = 0
            for minibatch in minibatches:
                mx, my = minibatch
                _, temp = sess.run([optimizer, cost] , feed_dict = {x:mx, y:my})
                lcost += temp
                cnt += 1
                if cnt %10 == 0:
                    print(temp)
            lcost = lcost/nums
            if i%10 == 0:
                print(i, lcost)
                costs.append(lcost)
        ypred = tf.argmax(fc3, axis = 1)
        yreal = tf.argmax(y, axis = 1)
        correct = tf.equal(ypred, yreal)
        accuracy = tf.reduce_mean(tf.cast(correct, 'float'))
        minibatches = random_minibatches(trainx, trainy, size = 64)
        train_acc = 0
        for minibatch in minibatches:
            mx, my = minibatch
            temp = accuracy.eval({x:mx, y:my})
            train_acc += temp
        train_acc = train_acc/nums
        test_acc = accuracy.eval({x:testx, y:testy})
        print(train_acc, test_acc)
        return train_acc, test_acc, params


_, _, params = model(trainx, trainy, testx, testy)


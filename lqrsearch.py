import control
import numpy as np

A = [[0,1],[0,0]]
B = [[0],[1]]
Q = [[10,0],[0,1]]
R = 0.01

Target = np.array([[31.6228,7.9527]])

def K(A, B, Q, R):
    return control.lqr(A, B, Q, R)[0]

elements = []
for q11 in [1,5,10,20,50,100,500,1000]:
    for q22 in [0.1,0.5,1.0,5.0,10.0]:
        for r in [0.001,0.01,0.1,1.0]:
            newQ = [[q11,0],[0,q22]]
            newR = r
            # print("q11:%.2f, q22:%.2f, r:%.2f => %s" % (q11, q22, r, K(A, B, newQ, newR)))
            elements.append([np.sum(np.abs(Target-K(A, B, newQ, newR))), q11, q22, r])

elements = sorted(elements, key = lambda item: item[0])
for item in elements:
    print(item)
#! /usr/bin/python

""" young tableau
   m x n matrix
"""
import sys

class element():
    def __init__(self, x, y):
        self.x = x
        self.y = y

def min_youngtableau(arry, p, m, n):
    minimum = element(p.x, p.y)
    if p.y < n and arry[p.x-1][p.y+1-1] < arry[p.x-1][p.y-1]:
        minimum.y = p.y + 1

    if p.x < m and arry[p.x+1-1][p.y-1] < arry[minimum.x-1][minimum.y-1]:
        minimum.x = p.x + 1
        minimum.y = p.y

    if minimum.x != p.x or minimum.y != p.y:
       temp = arry[p.x-1][p.y-1]
       arry[p.x-1][p.y-1] = arry[minimum.x-1][minimum.y-1]
       arry[minimum.x-1][minimum.y-1] = temp
       p = element(minimum.x, minimum.y)
       min_youngtableau(arry, p, m, n)

def extract_min(arry, m, n):
    temp = arry[1-1][1-1]
    arry[1-1][1-1] = 0xffff
    p = element(1,1)
    min_youngtableau(arry, p, m, n)
 
    return temp
    
def inseart(arry, v, m, n):
    if arry[m-1][n-1] != 0xffff:
        print "arrary is full"
        return

    arry[m-1][n-1] = v
    p = element(m, n)
    while p.x > 1 or p.y > 1: 
        maxmum = element(p.x, p.y)
        if p.x > 1 and arry[p.x-1-1][p.y-1] > arry[p.x-1][p.y-1]:
            maxmum.x = p.x - 1

        if p.y > 1  and arry[p.x-1][p.y-1-1] > arry[maxmum.x-1][maxmum.y-1]:
            maxmum.x = p.x
            maxmum.y = p.y-1

        if maxmum.x == p.x and maxmum.y == p.y:
           break

        temp = arry[p.x-1][p.y-1]
        arry[p.x-1][p.y-1] = arry[maxmum.x-1][maxmum.y-1]
        arry[maxmum.x-1][maxmum.y-1] = temp
        p = element(maxmum.x, maxmum.y)
       
def build_youngtaleau(arry, m, n):
    arry2 = [
        [0xffff, 0xffff, 0xffff],
        [0xffff, 0xffff, 0xffff],
        [0xffff, 0xffff, 0xffff],
        [0xffff, 0xffff, 0xffff],
    ]
    for i in range(m):
        for j in range(n):
            if arry[i][j] != 0xffff:
                inseart(arry2, arry[i][j], m, n)

    return arry2

def youngtableau_sort(arry, m, n):

    arry = build_youngtaleau(arry, m, n)
    result = []
    for i in range(m):
        for j in range(n):
            result.append(extract_min(arry, m, n))

    print result

if __name__ == '__main__':
    arry = [
        [12, 45, 50],
        [34, 54, 13],
        [77, 88, 99],
        [87, 0xffff, 0xffff],
    ]

    youngtableau_sort(arry, 4, 3)

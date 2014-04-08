#! /usr/bin/python

""" Heapsort
i as a argument specifying the number of elements starts from 1.
"""
import sys

counter = 0

def parent(i):
    return i/2

def left(i):
    return 2*i

def right(i):
    return 2*i+1

def max_heapify(arry, i, heap_size):
    global counter
    counter = counter + 1
    largest = i
    if left(i) <= heap_size  and arry[left(i)-1] > arry[i-1]:
        largest = left(i)
    if right(i) <= heap_size and arry[right(i)-1] > arry[largest-1]:
        largest = right(i)
    
    if largest != i:
        temp = arry[i-1]
        arry[i-1] = arry[largest-1]
        arry[largest-1] = temp
        max_heapify(arry, largest, heap_size)

def build_max_heap(arry, heap_size):
    i = heap_size/2
    while i >= 1:
        max_heapify(arry, i, heap_size)
        i = i-1

def Heapsort(arry):
    heap_size = len(arry)
    build_max_heap(arry, heap_size)
    
    while heap_size > 1:
        print arry 
        temp = arry[heap_size-1]
        arry[heap_size-1] = arry[0]
        arry[0] = temp
        heap_size = heap_size - 1
        max_heapify(arry, 1, heap_size)

    print "========================================"
    print arry

if __name__ == '__main__':
    #arry = [5, 13, 2, 25, 7, 17, 20, 8, 4]
    #arry = [2, 4, 5, 7, 8, 13, 17, 20, 25]
    arry =  [25, 20, 17, 13, 8, 7, 5, 4, 2]
    print arry
    print "========================================"
    Heapsort(arry)
    print "count:(%d)"%(counter) 

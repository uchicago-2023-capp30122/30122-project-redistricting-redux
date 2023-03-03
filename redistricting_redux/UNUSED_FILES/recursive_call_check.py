import time

def recursive_call(lb, ub):
    '''
    Testing the proper order of calls to be used in draw_recursive_map().
    '''
    time.sleep(0.2)
    print([lb, ub])
    if lb == ub:
        print(lb)
        return lb
    else:
        lower_median = (lb + ub) // 2
        upper_median = (lb + ub) // 2 + 1
        
        recursive_call(lb, lower_median)
        recursive_call(upper_median, ub)

if __name__ == '__main__':
    recursive_call(1, 14)
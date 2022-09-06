from memory_profiler import profile
'''
class A(object): 
    def __init__(self,x):
        self.x=x
'''        
class A(object):
    __slots__=('x')
    def __init__(self,x):
        self.x=x        
 
@profile
def main():
    f=[A(523825) for i in range(100000)]
 
if __name__=='__main__':
    main()
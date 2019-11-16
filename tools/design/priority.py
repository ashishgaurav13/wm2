from threading import Lock

class PriorityManager:

    def __init__(self, ordered = False, order = None):
        self.current_owner = None
        self.ordered = ordered
        if ordered:
            self.expecting = 0
            if order != None:
                self.expected_order = order
        self.mutex = Lock()
    
    def reset_order(self, new_order):
        self.expecting = 0
        self.expected_order = new_order

    def has_priority(self, name):
        ret_val = False
        self.mutex.acquire()
        ret_val = self.current_owner == name
        self.mutex.release()
        return ret_val
    
    def does_anyone_have_priority(self):
        ret_val = False
        self.mutex.acquire()
        ret_val = self.current_owner != None
        self.mutex.release()
        return ret_val

    # k is the priority number of who_is_asking
    def request_priority(self, who_is_asking, k = None):
        ret_val = False
        self.mutex.acquire()
        if who_is_asking == self.current_owner:
            ret_val = True
        elif self.current_owner == None:
            if self.ordered:
                if hasattr(self, 'expected_order') and \
                    self.expected_order[self.expecting] == k:
        
                    self.current_owner = who_is_asking
                    self.expecting += 1
                    ret_val = True
                elif not hasattr(self, 'expected_order') and \
                    k == self.expecting:

                    self.current_owner = who_is_asking
                    self.expecting += 1
                    ret_val = True
                else:
                    ret_val = False
            elif not self.ordered:
                self.current_owner = who_is_asking
                ret_val = True
    
        self.mutex.release()
        return ret_val
    
    def release_priority(self, who_has_it):
        ret_val = False
        self.mutex.acquire()
        if self.current_owner == who_has_it:
            # print('%s release' % self.current_owner)
            self.current_owner = None
            ret_val = True
        self.mutex.release()
        return ret_val        
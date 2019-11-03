from threading import Lock

class PriorityManager:

    def __init__(self):
        self.current_owner = None
        self.mutex = Lock()

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

    def request_priority(self, who_is_asking):
        ret_val = False
        self.mutex.acquire()
        if who_is_asking == self.current_owner:
            ret_val = True
        elif self.current_owner == None:
            self.current_owner = who_is_asking
            # print('%s acquire' % self.current_owner)
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
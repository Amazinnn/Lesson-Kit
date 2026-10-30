"""HTTP admission barrier. Bridge idle check runs after admitted writes finish."""
import threading


class Admission:
    def __init__(self):
        self.condition = threading.Condition()
        self.writes = 0
        self.handlers = 0
        self.closed = False
        self.final = False

    def enter(self, mutation):
        with self.condition:
            if self.final or mutation and self.closed:
                return False
            self.handlers += 1
            self.writes += int(mutation)
            return True

    def leave(self, mutation):
        with self.condition:
            self.handlers -= 1
            self.writes -= int(mutation)
            self.condition.notify_all()

    def prepare(self, close_bridge):
        with self.condition:
            if self.closed:
                return self.final
            self.closed = True
            self.condition.wait_for(lambda: self.writes == 0)
            if not close_bridge():
                self.closed = False
                return False
            self.final = True
            return True

    def drain(self):
        with self.condition:
            self.condition.wait_for(lambda: self.handlers == 0)

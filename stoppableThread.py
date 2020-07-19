import sys
import threading

class StopThread(StopIteration): pass

threading.SystemExit = SystemExit, StopThread

class StoppableThread(threading.Thread):
    def _bootstrap(self, stop_thread=False):
        def stop():
            nonlocal stop_thread
            stop_thread = True
        self.stop = stop

        def tracer(*_):
            if stop_thread:
                raise StopThread()
            return tracer
        sys.settrace(tracer)
        super()._bootstrap()
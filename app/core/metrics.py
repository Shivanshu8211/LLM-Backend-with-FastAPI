import time


class StreamMetrics:
    def __init__(self):
        self.start = time.perf_counter()
        self.first_token = None

    def mark_first_token(self):
        if self.first_token is None:
            self.first_token = time.perf_counter()

    @property
    def ttft(self):
        if self.first_token:
            return self.first_token - self.start
        return None

    @property
    def total_time(self):
        return time.perf_counter() - self.start

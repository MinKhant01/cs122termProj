class Stopwatch:
    def __init__(self):
        self.running = False
        self.time = 0
        self.laps = []

    def update_time(self):
        self.time += 1

    def get_time(self):
        minutes = self.time // 6000
        seconds = (self.time // 100) % 60
        sub_seconds = self.time % 100
        return f"{minutes:02}:{seconds:02}.{sub_seconds:02}"

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def reset(self):
        self.running = False
        self.time = 0
        self.laps.clear()

    def lap(self):
        self.laps.append(self.get_time())
        if len(self.laps) > 5:
            self.laps.pop(0)

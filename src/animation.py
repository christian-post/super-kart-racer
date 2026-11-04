class Animation:
    # loops through frames, a frame can be any object
    def __init__(self, frames, fps):
        self.frames = frames
        self.fps = fps
        self.elapsed = 0.0

    def update(self, dt, rate=1.0):
        self.elapsed += dt * rate

    @property
    def current(self):
        return self.frames[int(self.elapsed * self.fps) % len(self.frames)]
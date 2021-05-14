import os


class OSEnvHelper(object):
    def __init__(self):
        pass

    def get(self, env_var: str, default: str = "") -> str:
        return os.getenv(env_var, default)
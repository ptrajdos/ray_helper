import ray
import joblib
from joblib import Parallel, delayed
from joblib.parallel import get_active_backend
from ray.util.joblib import register_ray


class SharedArg:
    def __init__(self, obj):
        self.obj = obj
        self.ref = None

    def prepare(self):
        backend, _ = get_active_backend()

        backend_name = backend.__class__.__name__.lower()

        if "ray" in backend_name:
            if self.ref is None:
                self.ref = ray.put(self.obj)
            return self.ref

        return self.obj

    def resolve(self):
        if isinstance(self.obj, type(None)):
            return None

        if self.ref is not None:
            return ray.get(self.ref)

        return self.obj
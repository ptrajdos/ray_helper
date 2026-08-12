import time
import socket
from collections import Counter

import ray
from joblib import Parallel, delayed, parallel_backend
from ray.util.joblib import register_ray


# Connect to existing Ray cluster
try:
    ray.init(address="auto")
except Exception as e:
    print(f"Failed to connect to Ray cluster: {e}")
    print("Starting a new Ray cluster...")
    ray.init(ignore_reinit_error=True)
print("Ray resources:")
print(ray.cluster_resources())


# Enable Ray backend for Joblib
register_ray()


def work(i):
    import ray
    time.sleep(5)  # make tasks visible in htop
    return {
        "task": i,
        "host": socket.gethostname(),
        "node": ray.get_runtime_context().get_node_id(),
        "pid": __import__("os").getpid(),
    }


with parallel_backend("ray", n_jobs=-1):
    results = Parallel(verbose=10)(
        delayed(work)(i) for i in range(20)
    )


print("\nDistribution:")
print(Counter(r["host"] for r in results))

print("\nDetails:")
for r in results:
    print(r)
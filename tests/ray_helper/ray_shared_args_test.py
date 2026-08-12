import unittest

import joblib
import ray

from ray_helper._test_utils import worker
from ray_helper.ray_shared_args import SharedArg
from ray.util.joblib import register_ray

class RaySharedArgsTest(unittest.TestCase):

    def test_ray_shared_args(self):
        ray.init(ignore_reinit_error=True)
        register_ray()
        backends = ["loky", "ray"]
        for backend in backends:
            with self.subTest(backend=backend):
                with joblib.parallel_backend(backend, n_jobs=-1):
                    big_data = list(range(1000000))
                    shared = SharedArg(big_data)
                    prepared = shared.prepare()

                    results = joblib.Parallel()(
                        joblib.delayed(worker)(shared, x)
                        for x in range(10)
                    )

                    expected_results = [sum(big_data) + x for x in range(10)]
                    self.assertEqual(results, expected_results)
        self.assertTrue(True)
"""CLI entry points for managing Ray head/worker nodes."""

import argparse
import os
import subprocess
import sys


def _gb_to_bytes(gb):
    return gb * 1024 * 1024 * 1024


def _ray_cmd():
    """Return the path to the ``ray`` CLI executable."""
    return os.path.join(os.path.dirname(sys.executable), "ray")


def ray_head():
    parser = argparse.ArgumentParser(description="Start a Ray head node")
    parser.add_argument("--ip", default="127.0.0.1", help="Node IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6379, help="Ray port (default: 6379)")
    parser.add_argument("--dashboard-port", type=int, default=8265, help="Dashboard port (default: 8265)")
    parser.add_argument("--num-cpus", type=int, default=4, help="Number of CPUs (default: 4)")
    parser.add_argument("--memory-gb", type=int, default=10, help="Memory in GB (default: 10)")
    parser.add_argument("--object-store-gb", type=int, default=2, help="Object store memory in GB (default: 2)")
    args = parser.parse_args()

    ray = _ray_cmd()
    subprocess.run([ray, "stop"], check=False)
    sys.exit(subprocess.run([
        ray, "start", "--head",
        f"--node-ip-address={args.ip}",
        f"--port={args.port}",
        "--dashboard-host=0.0.0.0",
        f"--dashboard-port={args.dashboard_port}",
        f"--num-cpus={args.num_cpus}",
        f"--memory={_gb_to_bytes(args.memory_gb)}",
        f"--object-store-memory={_gb_to_bytes(args.object_store_gb)}",
    ]).returncode)


def ray_worker():
    parser = argparse.ArgumentParser(description="Start a Ray worker node")
    parser.add_argument("--ip", default="127.0.0.1", help="Head node IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6379, help="Ray port (default: 6379)")
    parser.add_argument("--num-cpus", type=int, default=4, help="Number of CPUs (default: 4)")
    parser.add_argument("--memory-gb", type=int, default=10, help="Memory in GB (default: 10)")
    parser.add_argument("--object-store-gb", type=int, default=2, help="Object store memory in GB (default: 2)")
    args = parser.parse_args()

    ray = _ray_cmd()
    subprocess.run([ray, "stop"], check=False)
    sys.exit(subprocess.run([
        ray, "start",
        f"--address={args.ip}:{args.port}",
        f"--num-cpus={args.num_cpus}",
        f"--memory={_gb_to_bytes(args.memory_gb)}",
        f"--object-store-memory={_gb_to_bytes(args.object_store_gb)}",
    ]).returncode)


def ray_stop():
    sys.exit(subprocess.run([_ray_cmd(), "stop"]).returncode)

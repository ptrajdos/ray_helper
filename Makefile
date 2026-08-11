ROOTDIR=$(realpath $(dir $(firstword $(MAKEFILE_LIST))))
UV := uv

SRCDIR=${ROOTDIR}/ray_helper
TESTDIR=${ROOTDIR}/tests
COVDIR=${ROOTDIR}/htmlcov_p
TOXDIR=${ROOTDIR}/.tox
COVERAGERC=${ROOTDIR}/.coveragerc
INSTALL_LOG_FILE=${ROOTDIR}/install.log
VENV_SUBDIR=${ROOTDIR}/venv
DOCS_DIR=${ROOTDIR}/docs


COVERAGE = coverage
UNITTEST_PARALLEL = unittest-parallel
PDOC= pdoc3
PYTHON=python
SYSPYTHON ?= python
PIP=pip
PYTEST=pytest
TOX=tox
TEE=tee
TOX_CORES=auto


LOGDIR=${ROOTDIR}/testlogs
LOGFILE=${LOGDIR}/`date +'%y-%m-%d_%H-%M-%S'`.log


.PHONY: clean

uv_install:
	$(SYSPYTHON) -m pip install --upgrade pip
	$(SYSPYTHON) -m pip install uv
# Default lock (PyPI)
uv.lock: uv_install
	$(UV) lock --index-strategy first-index

# Default install
pypackages: uv.lock
	RUST_LOG=debug $(UV) sync --extra test 2>&1 | $(TEE) $(INSTALL_LOG_FILE)
	touch $@

test: pypackages
	mkdir -p ${LOGDIR}  
	$(UV) run ${COVERAGE} run --branch  --source=${SRCDIR} -m unittest discover -p '*_test.py' -v -s ${TESTDIR} 2>&1 |tee -a ${LOGFILE}
	$(UV) run ${COVERAGE} html --show-contexts


test_parallel: pypackages
	mkdir -p ${COVDIR} ${LOGDIR}
	$(UV) run ${UNITTEST_PARALLEL} -j 0 --level test --disable-process-pooling -v -t ${ROOTDIR} -s ${TESTDIR} -p '*_test.py' --coverage --coverage-rcfile ./.coveragerc --coverage-source ${SRCDIR} --coverage-html ${COVDIR}  2>&1 |tee -a ${LOGFILE}

docs: pypackages
	$(UV) run $(PDOC) --force --html ${SRCDIR} --output-dir ${DOCS_DIR}

profile: pypackages
	
	$(UV) run ${PYTEST} -n auto --cov-report=html --cov=${SRCDIR} --profile ${TESTDIR}

tox_check: pypackages
	$(UV) run ${TOX} -p ${TOX_CORES} 

clean: clean_tox
	rm -rf .venv uv.lock

clean_tox:
	rm -rf ${TOXDIR}

#TODO move this to python scripts probably
RAY_PORT ?= 6379
RAY_DASHBOARD_PORT ?= 8265
RAY_NUM_CPUS ?= 4
IP ?= 127.0.0.1
RAY_MEMORY_GB ?= 10
RAY_OBJECT_STORE_GB ?= 2

RAY_MEMORY := $(shell echo "$$(( $(RAY_MEMORY_GB) * 1024 * 1024 * 1024 ))")
RAY_OBJECT_STORE_MEMORY := $(shell echo "$$(( $(RAY_OBJECT_STORE_GB) * 1024 * 1024 * 1024 ))")
# Start Ray head node (manager)
ray-head:
	$(UV) run ray stop || true
	$(UV) run ray start --head \
		--node-ip-address=$(IP) \
		--port=$(RAY_PORT) \
		--dashboard-host=0.0.0.0 \
		--dashboard-port=$(RAY_DASHBOARD_PORT) \
		--num-cpus=$(RAY_NUM_CPUS) \
		--memory=$(RAY_MEMORY) \
		--object-store-memory=$(RAY_OBJECT_STORE_MEMORY)

# Start Ray worker node
# Usage: make ray-worker IP=<head-node-ip>
ray-worker:
	$(UV) run ray stop || true
	$(UV) run ray start \
		--address=$(IP):$(RAY_PORT) \
		--num-cpus=$(RAY_NUM_CPUS) \
		--memory=$(RAY_MEMORY) \
		--object-store-memory=$(RAY_OBJECT_STORE_MEMORY)

ray-stop:
	$(UV) run ray stop
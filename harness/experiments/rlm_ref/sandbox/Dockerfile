# The code environment of the authors' RLM (rlms 0.1.3, environment="docker"; B4, D73 Q46).
# The package's default image, python:3.11-slim, pinned by its registry digest (pulled 15 October 2026, Python 3.11.17),
# with the two packages DockerREPL.setup installs (dill, requests) preinstalled from hash-pinned requirements
# (requirements.txt, uv pip compile --generate-hashes --exclude-newer 2026-10-14). setup's own
# "pip install -q dill requests" then finds both present and downloads nothing (check_rlm_ref.py runs it offline).
# Built by experiments/rlm_ref/adapter.py build_image(), which labels the image with this file's and the
# requirements' sha256; a run refuses an image whose labels differ and passes the image by its content id.
FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check --require-hashes --only-binary :all: \
        -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

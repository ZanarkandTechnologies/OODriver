FROM python:3.10-bullseye

ARG CARLA_PYTHON_VERSION=0.9.16
ARG INSTALL_TORCH=0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    SDL_VIDEODRIVER=dummy

WORKDIR /workspace/0xDriver

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --default-timeout=1000 --retries=10 \
    "carla==${CARLA_PYTHON_VERSION}" \
    "dictor==0.1.12" \
    "ephem==4.1.5" \
    "filterpy==1.4.5" \
    "jsonpickle==3.0.3" \
    "lxml==5.1.0" \
    "matplotlib==3.5.3" \
    "networkx==3.4.2" \
    "numpy==1.26.4" \
    "opencv-python-headless==4.6.0.66" \
    "pexpect==4.9.0" \
    "Pillow==10.2.0" \
    "psutil==5.9.8" \
    "py-trees==0.8.3" \
    "pygame==2.6.0" \
    "rdp==0.8" \
    "requests==2.31.0" \
    "scipy==1.14.1" \
    "shapely==2.0.4" \
    "simple_watchdog_timer==0.1.1" \
    "six==1.16.0" \
    "tabulate==0.9.0" \
    "transforms3d==0.4.1" \
    "ujson==5.9.0" \
    "xmlschema==1.0.18"

RUN if [ "${INSTALL_TORCH}" = "1" ]; then \
      python -m pip install --default-timeout=1000 --retries=10 \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.5.0" "torchvision==0.20.0"; \
    fi

CMD ["python", "-c", "import carla, numpy; print('fail2drive-client-ready')"]

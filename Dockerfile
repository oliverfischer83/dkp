FROM python:3.12-slim

ARG USERNAME=dkpuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

WORKDIR /app

COPY src /app
COPY config.yml /app
COPY pyproject.toml /app
COPY requirements.in /app
COPY requirements-dev.in /app
COPY requirements.txt /app
COPY LICENSE /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

RUN chown -R $USERNAME:$USERNAME /app
USER $USERNAME

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

# copy data after pip install to avoid error due to multiple top-level packages found during build
COPY data ./dkp/data

EXPOSE 8501
CMD ["streamlit", "run", "/app/dkp/streamlit/01_overview.py"]

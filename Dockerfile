FROM python:3.12-slim

WORKDIR /app

COPY src ./src
COPY data ./data
COPY config.yml .
COPY pyproject.toml .
COPY requirements.in .
COPY requirements-dev.in .
COPY requirements.txt .
COPY LICENSE .

ARG USERNAME=dkpuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
RUN chown -R $USERNAME:$USERNAME /app
USER $USERNAME

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

EXPOSE 8501
CMD ["streamlit", "run", "/app/src/dkp/streamlit/01_overview.py"]

# dkp

## setup environment

```bash
conda create -n dkp python=3.12 -y
conda activate dkp
pip install pip-tools
pip-compile --all-extras pyproject.toml
pip-sync
```

## start server

```bash
streamlit run frontend/01_overview.py
```


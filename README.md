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
cd /home/fio1be/Projects/private/dkp  # path to repository root dir
python -m streamlit run frontend/01_overview.py
```


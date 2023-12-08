# server-backup-example

## poetry install
```
curl -sSL https://install.python-poetry.org | python3 -
poetry install
poetry shell
```

## Crontab job at 3am daily

```
0 3 * * * cd /home/user/server-backup-example; /home/user/.local/bin/poetry run python src/main.py
```
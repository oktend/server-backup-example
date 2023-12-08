# server-backup

## Crontab job at 3am daily

```
0 3 * * * . $(cd /home/user/server-backup; /home/user/.local/bin/poetry env info --path)/bin/activate; cd /home/user/server-backup; poetry install; python src/main.py
```
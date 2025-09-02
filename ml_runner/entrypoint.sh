#!/bin/bash
set -e
service ssh start
jupyter notebook --ip 0.0.0.0 --port 8888 --no-browser --allow-root --notebook-dir=/app/workflows --NotebookApp.token= &
wait

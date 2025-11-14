#!/bin/bash
set -e

# Start SSH server
if [ "$SSH_SERVER_ENABLED" = "true" ]; then
    service ssh start
fi

# Start Jupyter server
if [ "$JUPYTER_SERVER_ENABLED" = "true" ]; then
    jupyter notebook --ip 0.0.0.0 --port 8888 --no-browser --allow-root --notebook-dir=/app/workflows --NotebookApp.token= &
fi

# Run the command provided as an argument
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    # If no command is provided and no services are enabled, just keep container running
    tail -f /dev/null
fi

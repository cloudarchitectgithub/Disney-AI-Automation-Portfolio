FROM chromadb/chroma:0.4.18

# Fix NumPy compatibility by pinning to 1.x
RUN pip install --no-cache-dir 'numpy<2.0' --force-reinstall

# Prevent the entrypoint from rebuilding hnswlib (which pulls NumPy 2.0)
# Create a custom startup script
RUN echo '#!/bin/bash\n\
set -e\n\
# Skip the hnswlib rebuild that causes NumPy 2.0 to be installed\n\
exec uvicorn chromadb.app:app --host 0.0.0.0 --port 8000 --workers 1 --log-config chromadb/log_config.yml\n\
' > /custom_entrypoint.sh && chmod +x /custom_entrypoint.sh

ENTRYPOINT ["/custom_entrypoint.sh"]

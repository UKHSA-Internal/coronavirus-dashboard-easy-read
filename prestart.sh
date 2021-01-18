echo "Running entrypoint.py"
python /entrypoint.py
supervisorctl restart nginx


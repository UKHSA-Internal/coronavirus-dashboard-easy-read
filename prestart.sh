echo "Running entrypoint.py"
python /prestart.py
supervisorctl restart nginx


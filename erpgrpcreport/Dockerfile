FROM python:3.11.9-slim-bullseye

WORKDIR /app

# copy requirements and pre-downloaded wheels (if any)
COPY erpgrpcreport/requirements.txt /app/requirements.txt
# copy wheels placed in erpgrpcreport/wheels (created by fetch_wheels scripts)
COPY erpgrpcreport/wheels /app/wheels

# If wheels are available, install from local wheels; otherwise fall back to network install
RUN if [ -d /app/wheels ] && [ "$(ls -A /app/wheels)" ]; then \
		pip install --no-index --find-links /app/wheels -r /app/requirements.txt; \
	else \
		pip install --no-cache-dir -r /app/requirements.txt; \
	fi

# copy package and top-level pb generated files (they are in project root)
COPY erpgrpcreport /app/erpgrpcreport
COPY *.py /app/
COPY *_pb2*.py /app/

ENV PYTHONPATH=/app
EXPOSE 8081

CMD ["python", "-m", "erpgrpcreport.app"]

# Use an explicit, stable tag to avoid flaky remote tag resolution
# e.g. python:3.11.9-slim-bullseye is explicit and commonly available
FROM python:3.11.9-slim-bullseye

WORKDIR /app

# copy requirements first to leverage Docker layer cache when requirements don't change
COPY requirements.txt /app/requirements.txt

# copy pre-downloaded wheels (if any) into image; users can run fetch_wheels to populate ./wheels
COPY wheels /app/wheels
# also copy per-package wheels if present
COPY erpgrpcreport/wheels /app/erpgrpcreport_wheels

# If wheels are available, install from local wheels; otherwise fall back to network install
RUN if [ -d /app/wheels ] && [ "$(ls -A /app/wheels)" ]; then \
			pip install --no-index --find-links /app/wheels -r /app/requirements.txt; \
		elif [ -d /app/erpgrpcreport_wheels ] && [ "$(ls -A /app/erpgrpcreport_wheels)" ]; then \
			pip install --no-index --find-links /app/erpgrpcreport_wheels -r /app/requirements.txt; \
		else \
			pip install --no-cache-dir -r /app/requirements.txt; \
		fi

# copy rest of the application
COPY . /app

RUN chmod +x /app/start.sh || true

# expose grpc and admin ports
EXPOSE 50051 8080

ENV FLASK_ENV=production

CMD ["/app/start.sh"]
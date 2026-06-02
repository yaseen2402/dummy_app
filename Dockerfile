# --------------------------------------------------------
# STAGE 1: Download Dynatrace OneAgent
# --------------------------------------------------------
# This stage uses the Dynatrace API to download the OneAgent binary.
FROM alpine:latest AS agent-downloader

# These ARG values must be passed during `docker build` using --build-arg
ARG DT_API_URL
ARG DT_API_TOKEN

# Install curl
RUN apk add --no-cache curl unzip

# Download OneAgent
WORKDIR /downloads
RUN curl -s -O -H "Authorization: Api-Token $DT_API_TOKEN" \
    "$DT_API_URL/v1/deployment/installer/agent/unix/paas/latest?flavor=default&include=python" && \
    mkdir -p /opt/dynatrace/oneagent && \
    unzip -q -d /opt/dynatrace/oneagent latest*


# --------------------------------------------------------
# STAGE 2: Build the Actual Application
# --------------------------------------------------------
FROM python:3.12-slim

# Copy OneAgent from the downloader stage
COPY --from=agent-downloader /opt/dynatrace/oneagent /opt/dynatrace/oneagent

# Tell the OneAgent where to find the Python executable (it intercepts it)
ENV LD_PRELOAD=/opt/dynatrace/oneagent/agent/lib64/liboneagentproc.so

# Set up the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY app.py .

# Expose the port (Cloud Run defaults to 8080, but our app runs on 5000, 
# so we tell Cloud Run to use 5000)
EXPOSE 5000

# The OneAgent intercepts standard executions, so we just run python normally
CMD ["python", "app.py"]

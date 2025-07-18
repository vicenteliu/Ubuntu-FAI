# Ubuntu FAI Build System Docker Image
# Multi-stage build for reproducible Ubuntu 24.04 ISO generation

# Build stage - Install dependencies and setup environment
FROM ubuntu:24.04@sha256:b359f1067efa76f37863778f7b6d0e8d911e3ee8efa807ad01fbf5dc1ef9006b AS builder

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package list and install core dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3-pip \
    python3.12-venv \
    fai-server \
    fai-client \
    fai-cd \
    debootstrap \
    squashfs-tools \
    isolinux \
    syslinux \
    genisoimage \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create Python symlink for consistency
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python

# Production stage - Minimal runtime environment
FROM ubuntu:24.04@sha256:b359f1067efa76f37863778f7b6d0e8d911e3ee8efa807ad01fbf5dc1ef9006b AS production

ENV DEBIAN_FRONTEND=noninteractive

# Copy installed packages from builder stage
COPY --from=builder /usr/bin/python* /usr/bin/
COPY --from=builder /usr/lib/python3.12 /usr/lib/python3.12
COPY --from=builder /usr/share/fai /usr/share/fai
COPY --from=builder /usr/bin/fai-* /usr/bin/
COPY --from=builder /usr/sbin/fai-* /usr/sbin/

# Install only runtime dependencies in production stage
RUN apt-get update && apt-get install -y \
    python3-pip \
    fai-server \
    fai-client \
    fai-cd \
    debootstrap \
    squashfs-tools \
    isolinux \
    syslinux \
    genisoimage \
    curl \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1001 fai && \
    useradd --uid 1001 --gid fai --shell /bin/bash --create-home fai && \
    echo 'fai ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies as root, then switch to fai user
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/fai-config /tmp/fai-build && \
    chown -R fai:fai /app /tmp/fai-build

# Switch to non-root user for security
USER fai

# Copy application code
COPY --chown=fai:fai . .

# Expose volume mount points
VOLUME ["/app/output", "/app/config"]

# Default command
CMD ["python3", "build.py", "--help"]
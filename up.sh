#!/bin/bash
REDIS_PASSWORD=$(openssl rand -hex 32) \
  docker compose up $@
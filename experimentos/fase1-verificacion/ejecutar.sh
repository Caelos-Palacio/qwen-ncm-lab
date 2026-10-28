#!/bin/sh
set -eu
cd /home/carlos/qwen-ncm-lab/experimentos/fase1-verificacion
exec flock -n -E 75 /tmp/qwen-proyectos-compute.lock timeout 600 /home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/bin/python diagnosticar.py

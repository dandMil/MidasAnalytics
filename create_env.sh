#!/bin/bash

ENV_NAME="MidasAnalytics"

echo "Creating conda environment: $ENV_NAME"
conda env create -f environment.yml

echo "Activating environment..."
conda activate $ENV_NAME

echo "Done. To activate manually in future:"
echo "    conda activate $ENV_NAME"

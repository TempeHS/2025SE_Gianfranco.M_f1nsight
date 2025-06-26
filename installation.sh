#!/bin/bash

#create python virtual environment 
echo "loading..."
python3 -m venv .venv
source .venv/bin/activate

#install requirements
pip install -r requirements.txt

echo "installation complete!"
echo "run 'run.py' to launch website"

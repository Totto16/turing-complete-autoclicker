#!/usr/bin/env bash

# change in python and here!!
LANG="deu"

if [[ ! -d "env" ]]; then
    python3 -m venv env
    pip install -r requirements.txt
fi

if [[ ! -f "$LANG.traineddata" ]]; then
    wget "https://github.com/tesseract-ocr/tessdata/raw/main/$LANG.traineddata"
fi

source env/bin/activate

## to save dependecies
# python3 -m pip freeze > requirements.txt

## to deactivate:
# deactivate

python3 src/main.py

## to type check with a tool
# mypy src/main.py

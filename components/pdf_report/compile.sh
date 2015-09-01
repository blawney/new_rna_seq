#!/bin/bash

f=$1
pdflatex $f
bibtex $f
pdflatex $f
pdflatex $f

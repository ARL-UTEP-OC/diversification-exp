#!/bin/bash

opam switch 4.01.0
eval `opam config env`

./amoeba_exp.py $1

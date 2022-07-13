#!/bin/bash

while read p; do
  python prob_phys_units.py $p
done <cpp_files_1.txt

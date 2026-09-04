#!/usr/bin/env bash
# fetch_hai.sh - download HAI 20.07 and verify it byte for byte.
# HAI is NOT redistributed here. It belongs to the Affiliated Institute of
# ETRI, CC BY 4.0. Pinned to a commit, not a branch, so upstream content
# cannot move under a published result.
# The sha256 values were measured in Claude's container 2026-09-03. A mismatch
# is a finding. Report it, do not repin.
# The technical details PDF is fetched too (CC BY-SA 4.0, not redistributed).
# It publishes the attack count per test file - HAI 20.07 has 38 scenarios,
# 28 in test1 and 10 in test2 - which verify_hai.py asserts as an EXTERNAL
# check: a number from the dataset authors rather than one this repository
# measured and then compared against itself.
set -euo pipefail
C=2a814cebc9a66b06c9e5cd545e2d72e65d383737
B=https://raw.githubusercontent.com/icsdataset/hai/$C/hai-20.07
R=https://raw.githubusercontent.com/icsdataset/hai/$C
mkdir -p data
printf '%s\n' \
"376e8288a5e3cf69bc5c506f75d6fb9cebb30ff43326c60ed675ccea37700844  train1.csv.gz" \
"30caafaeba9736238fe746a780c0baf3aa71ee7bcf494fb3daf721128ad7fdde  train2.csv.gz" \
"68cc18af44efcd756e9eaaa81790855836e8aee3f2ce9c4d9dd95a0ada36c2e4  test1.csv.gz" \
"427841d8240d5fa557fb28ed58da21bb93d0a3c2b30e43b82ab2d816330185e2  test2.csv.gz" \
"0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556  hai_dataset_technical_details.pdf" \
> data/SHA256SUMS
for f in train1 train2 test1 test2; do
  if [ -f "data/$f.csv.gz" ]; then
    echo "have  $f.csv.gz"
  else
    echo "get   $f.csv.gz"
    curl -fSL --retry 3 -o "data/$f.csv.gz" "$B/$f.csv.gz"
  fi
done
if [ -f "data/hai_dataset_technical_details.pdf" ]; then
  echo "have  hai_dataset_technical_details.pdf"
else
  echo "get   hai_dataset_technical_details.pdf"
  curl -fSL --retry 3 -o "data/hai_dataset_technical_details.pdf" "$R/hai_dataset_technical_details.pdf"
fi
echo
cd data
sha256sum -c SHA256SUMS
echo
echo "OK - five files verified against pinned commit $C"
echo "Files stay gzipped. train1 is 130293220 bytes uncompressed."
echo "Read with gzip.open; do not decompress to disk."

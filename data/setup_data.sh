#!/bin/bash

set -e


mkdir -p archives


# Folders in tar

echo

DOWNLOADS=(
    "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz,midi,lmd_matched"
)

for entry in "${DOWNLOADS[@]}"; do
  IFS="," read -r URL EXTRACTDIR EXTRACT <<< "$entry"
  
  ARCHIVE="archives/$(basename $URL)"
  mkdir -p "$EXTRACTDIR"

  if [ ! -f "$ARCHIVE" ]; then
    echo "• Downloading $URL..."
    wget "$URL" -O "$ARCHIVE"
  else
    echo "• File $ARCHIVE already exists, skipping..."
  fi

  if [ ! -d "$EXTRACTDIR/$EXTRACT" ]; then
    cd "$EXTRACTDIR"

    echo "• Extracting $ARCHIVE to $EXTRACTDIR..."
    tar -xf "../$ARCHIVE"

    cd - > /dev/null 
  else
    echo "• Folder $EXTRACTDIR/$EXTRACT already exists, skipping..."
  fi
done


# Plain files

echo

DOWNLOADS=(
    "http://hog.ee.columbia.edu/craffel/lmd/md5_to_paths.json,midi"
    "http://hog.ee.columbia.edu/craffel/lmd/match_scores.json,midi"
    "https://www.ifs.tuwien.ac.at/mir/msd/partitions/msd-MAGD-genreAssignment.cls,genre"
    "https://www.ifs.tuwien.ac.at/mir/msd/partitions/msd-topMAGD-genreAssignment.cls,genre"
    "https://www.ifs.tuwien.ac.at/mir/msd/partitions/msd-MASD-styleAssignment.cls,genre"
)

for entry in "${DOWNLOADS[@]}"; do
  IFS="," read -r URL DOWNLOADDIR <<< "$entry"
  
  mkdir -p "$DOWNLOADDIR"
  cd "$DOWNLOADDIR"

  if [ ! -f "$(basename "$URL")" ]; then
    echo "• Downloading $URL..."
    wget "$URL"
  else
    echo "• File from $URL already exists, skipping..."
  fi

  cd - > /dev/null
done


# Files in zip

echo

DOWNLOADS=(
  "https://www.tagtraum.com/genres/msd_tagtraum_cd1.cls.zip,genre,msd_tagtraum_cd1.cls"
  "https://www.tagtraum.com/genres/msd_tagtraum_cd2.cls.zip,genre,msd_tagtraum_cd2.cls"
  "https://www.tagtraum.com/genres/msd_tagtraum_cd2c.cls.zip,genre,msd_tagtraum_cd2c.cls"
)

for entry in "${DOWNLOADS[@]}"; do
  IFS="," read -r URL EXTRACTDIR EXTRACT <<< "$entry"
  
  ARCHIVE="archives/$(basename $URL)"
  mkdir -p "$EXTRACTDIR"

  if [ ! -f "$ARCHIVE" ]; then
    echo "• Downloading $URL..."
    wget "$URL" -O "$ARCHIVE"
  else
    echo "• File $ARCHIVE already exists, skipping..."
  fi

  if [ ! -f "$EXTRACTDIR/$EXTRACT" ]; then
    cd "$EXTRACTDIR"

    echo "• Extracting $ARCHIVE to $EXTRACTDIR..."
    unzip "../$ARCHIVE"

    cd - > /dev/null
  else
    echo "• Extracted file $EXTRACTDIR/$EXTRACT already exists, skipping..."
  fi
done

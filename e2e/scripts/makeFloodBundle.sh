#!/bin/bash
# get parameters
cd $(dirname ${BASH_SOURCE})
while getopts ":d:" opt; do
  case $opt in
    d) output="$OPTARG"
    ;;
    \?) echo "Invalid argument $opt"
    ;;
  esac
done

# go to source code
cd ../src

if [ ! -d flood/simulation ]; then
  mkdir -p flood/simulation;
fi
if [ ! -d flood/generation ]; then
  mkdir -p flood/generation;
  mkdir -p flood/generation/documents;
fi
if [ ! -d flood/forms ]; then
  mkdir -p flood/forms;
fi

# add ALL dependencies outside of `src/flood` here
cp api.ts flood/simulation;
cp generation/Claim.ts flood/generation;
cp generation/documents/index.ts flood/generation/documents;
cp ../forms/hcp-real.pdf flood/forms;

# conditional command syntax
# https://stackoverflow.com/questions/43171648/sed-gives-sed-cant-read-no-such-file-or-directory
_SED="sed -i"
if [[ "$OSTYPE" == "darwin"* ]]; then
  _SED="sed -i ''"
fi

# this is currently just for "flood/generation/documents/*.ts"
for ff in flood/*/*/*.ts; do
  $_SED -e 's|"\.\./\.\./api"|"\.\./\.\./simulation/api"|g' $ff
done
for ff in flood/*/*.ts; do
  $_SED -e 's|"\.\./\.\./generation/Claim"|"\.\./generation/Claim"|g' $ff
  $_SED -e 's|"\.\./\.\./api"|"\.\./simulation/api"|g' $ff
  # this is only for "generation/Claim.ts"
  $_SED -e 's|"\.\./api"|"\.\./simulation/api"|g' $ff
done
for f in flood/*.ts; do
  $_SED -e 's|"\.\./generation/Claim"|"\./generation/Claim"|g' $f
  $_SED -e 's|"\.\./api"|"\./simulation/api"|g' $f
done

# clear previous builds
cd ../scripts
if [[ -d $output ]]; then
  if [[ -f $output/floodBundle.zip ]]; then
    rm $output/floodBundle.zip
  fi
  if [[ -f $output/index.perf.ts ]]; then
    rm $output/index.perf.ts
  fi
else
  mkdir $output
fi

# build `.zip` flood bundle
cd ../src/flood
zip -9 -r ../../scripts/$output/floodBundle.zip * -x '*index.perf.ts' '*tmp*' '*.git*' '*.md' '*.DS_Store'
cd ..

# copy index.perf.ts into scripts/ folder
cp flood/index.perf.ts ../scripts/$output

# change import paths back to original 
# (not needed for external files, cause they get deleted)
for ff in flood/*/*.ts; do
  $_SED -e 's|"\.\./generation/Claim"|"\.\./\.\./generation/Claim"|g' $ff
  $_SED -e 's|"\.\./simulation/api"|"\.\./\.\./api"|g' $ff
done
for f in flood/*.ts; do
  $_SED -e 's|"\./generation/Claim"|"\.\./generation/Claim"|g' $f
  $_SED -e 's|"\./simulation/api"|"\.\./api"|g' $f
done

# remove temporary folders
rm -rf flood/simulation/
rm -rf flood/generation/
rm -rf flood/forms/

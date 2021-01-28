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
if [ ! -d flood/forms ]; then
  mkdir -p flood/forms;
fi

# add all dependencies outside of `src/flood` here
cp api.ts flood/simulation;
cp simulation/types.ts flood/simulation;
cp simulation/documents.ts flood/simulation;
cp ../forms/hcp-real.pdf flood/forms;

# conditional command syntax 
# https://stackoverflow.com/questions/43171648/sed-gives-sed-cant-read-no-such-file-or-directory
_SED=""
if [[ "$OSTYPE" == "darwin"* ]]; then
  _SED="sed -i ''"
else
  _SED="sed -i"
fi

# change import paths to link to `src/flood/simulation`
$_SED -e 's|"\.\./api"|"\./api"|g' flood/simulation/types.ts

for ff in flood/*/*.ts; do
  $_SED -e 's|"\.\./\.\./simulation/types"|"\.\./simulation/types"|g' $ff
  $_SED -e 's|"\.\./\.\./api"|"\.\./simulation/api"|g' $ff
done
for f in flood/*.ts; do
  $_SED -e 's|"\.\./simulation/types"|"\./simulation/types"|g' $f
  $_SED -e 's|"\.\./api"|"\./simulation/api"|g' $f
done

# clear previous builds
cd ../scripts
rm -rf $output
mkdir $output

# build `.zip` flood bundle
cd ../src/flood
zip -9 -r ../../scripts/$output/floodBundle.zip * -x '*index.perf.ts' '*tmp*' '*.git*' '*.md' '*.DS_Store'
cd ..

# copy index.perf.ts into scripts/ folder
cp flood/index.perf.ts ../scripts/$output

# change import paths back to original
for ff in flood/*/*.ts; do
  $_SED -e 's|"\.\./simulation/types"|"\.\./\.\./simulation/types"|g' $ff
  $_SED -e 's|"\.\./simulation/api"|"\.\./\.\./api"|g' $ff
done
for f in flood/*.ts; do
  $_SED -e 's|"\./simulation/types"|"\.\./simulation/types"|g' $f
  $_SED -e 's|"\./simulation/api"|"\.\./api"|g' $f
done

# remove temporary `src/flood/simulation` folder
rm -rf flood/simulation/
# remove temporary `src/flood/forms` folder
rm -rf flood/forms/

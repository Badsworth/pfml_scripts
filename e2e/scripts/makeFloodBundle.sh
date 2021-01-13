#!/usr/bin/env bash

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

# change import paths to link to `src/flood/simulation`
sed -i '' -e 's|"\.\./api"|"\./api"|g' flood/simulation/types.ts

for ff in flood/*/*.ts; do
  sed -i '' -e 's|"\.\./\.\./simulation/types"|"\.\./simulation/types"|g' $ff
  sed -i '' -e 's|"\.\./\.\./api"|"\.\./simulation/api"|g' $ff
done
for f in flood/*.ts; do
  sed -i '' -e 's|"\.\./simulation/types"|"\./simulation/types"|g' $f
  sed -i '' -e 's|"\.\./api"|"\./simulation/api"|g' $f
done

# clear previous builds
rm -rf ../scripts/floodBundle.zip
rm -rf ../scripts/index.perf.ts

# build `.zip` flood bundle
cd flood/
zip -r ../../scripts/floodBundle.zip * -x '*index.perf.ts' '*tmp*' '*claims_*' '*.git*' '*.md' '*.DS_Store'
cd ..

# copy index.perf.ts into scripts/ folder
cp flood/index.perf.ts ../scripts

# change import paths back to original
for ff in flood/*/*.ts; do
  sed -i '' -e 's|"\.\./simulation/types"|"\.\./\.\./simulation/types"|g' $ff
  sed -i '' -e 's|"\.\./simulation/api"|"\.\./\.\./api"|g' $ff
done
for f in flood/*.ts; do
  sed -i '' -e 's|"\./simulation/types"|"\.\./simulation/types"|g' $f
  sed -i '' -e 's|"\./simulation/api"|"\.\./api"|g' $f
done

# remove temporary `src/flood/simulation` folder
rm -rf flood/simulation/
# remove temporary `src/flood/forms` folder
rm -rf flood/forms/

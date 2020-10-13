#!/usr/bin/env bash

cd ../src

if [ ! -d flood/simulation ]; then
  mkdir -p flood/simulation;
fi

cp api.ts flood/simulation;
cp simulation/types.ts flood/simulation;

sed -i '' -e 's|"\.\./api"|"\./api"|g' flood/simulation/types.ts

for f in flood/*/*.ts; do
  sed -i '' -e 's|"\.\./\.\./simulation/types"|"\.\./simulation/types"|g' $f
done

sed -i '' -e 's|"\.\./simulation/types"|"\./simulation/types"|g' flood/config.ts

rm -rf ../../scripts/floodBundle.zip

cd flood/

zip -r ../../scripts/floodBundle.zip * -x '*index.perf.ts' '*tmp*' '*.git*' '*.md' '*.DS_Store'

for f in */*.ts; do
  sed -i '' -e 's|"\.\./simulation/types"|"\.\./\.\./simulation/types"|g' $f
done

sed -i '' -e 's|"\./simulation/types"|"\.\./simulation/types"|g' config.ts

cp index.perf.ts ../../scripts;
sed -i '' -e 's|"\.\./simulation/types"|"\./simulation/types"|g' ../../scripts/index.perf.ts

rm -rf simulation/

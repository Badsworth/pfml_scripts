# How to run Element scripts

- You need a `data` folder inside `src/flood`
- The `data` folder needs to contain a `claims.json` with all scenario data.
- Now when you run `npm run flood:plan` it should go through all scenarios in that `claims.json` file and show steps it could possibly run.

# Deploying Element scripts

Flood takes a `.zip` and exports it in the same directory as our main script, but our codebase is importing some files outside our `src/flood` folder, which causes import paths to be wrong and errors to occur due to missing files.

The workaround for this is keeping the `scripts/makeFloodBundle.sh` script updated with _outsider files_ we import - `makeFloodBundle` copies all external dependencies into a `src/flood/simulation` folder, adjusts all those import paths, and creates the `.zip` we need.

### To deploy:

- Have access to a paid Flood account, or someone that has one and invites you.
- Generate the dataset for the run using the generate commands and submit employers/employees to be added to the respective environments this LST is going to run against.
- Run the build script: `scripts/makeFloodBundle.sh` or `npm run flood:build`.
  - Inside the `.zip` archive will be:
    - Everything inside the `src/flood` folder, **except**:
      - `index.perf.ts`, it is uploaded separately
      - `tmp` folders, get generated locally, but are irrelevant
      - Other irrelevant files such as `deployment.md` this one.
    - External file/scripts dependencies, as of 6th November 2020:
      - `src/simulation/types.ts` which depends on `src/api.ts`
      - `src/simulation/documents.ts`
      - `src/api.ts`
- Login in to Flood, create a new Stream.
- On the "Design" tab:
  - Choose "Script Upload"
  - Upload the `.zip` and the `index.perf.ts` files added to the `scripts/` folder.
  - Make sure you click on the "Element" logo
- On the "Launch" tab:
  - Pick "Demand"
  - Pick a "Region"
  - Select "Parameters" of this Load & Stress Test
    - Time duration
    - User concurrency
    - User Ramp up time (_important_)
  - Click "Launch Test"
- Wait for the script to start running...
- No red warning icon? Success!
- Otherwise, check "Archived Results" for error logging info

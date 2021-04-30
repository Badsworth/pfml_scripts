import ClaimPool from "../generation/Claim";
import { PostSubmitCallback, submit } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import path from "path";
import {
  approveClaim,
  withFineosBrowser,
  denyClaim,
  closeDocuments,
} from "../submission/PostSubmit";
import chalk from "chalk";
import dataDirectory from "../generation/DataDirectory";

const setConcurrency = (requested: number) => {
  if (requested <= 10 && requested > 0) return requested;
  else throw Error("Concurrency must be in range 1-10");
};

(async () => {
  const args = process.argv;
  let concurrency = 0;
  let dataDir: string;
  const number = parseInt(args[args.length - 1]);

  // if concurrency is not specified assign arg value to dataDir
  if (Number.isNaN(number)) {
    dataDir = args[args.length - 1];
  } else {
    dataDir = args[args.length - 2];
    concurrency = setConcurrency(number);
  }

  const storage = dataDirectory(dataDir);
  const tracker = new ClaimSubmissionTracker(storage.state);
  const claimPool: ClaimPool = await ClaimPool.load(
    storage.claims,
    storage.documents
  );

  const postSubmit: PostSubmitCallback = async (claim, response) => {
    const { metadata } = claim;
    if (metadata && "postSubmit" in metadata) {
      // Open a puppeteer browser for the duration of this callback.
      await withFineosBrowser(async (page) => {
        const { fineos_absence_id } = response;
        if (!fineos_absence_id)
          throw new Error(
            `No fineos_absence_id was found on this response: ${JSON.stringify(
              response
            )}`
          );
        switch (metadata.postSubmit) {
          case "APPROVE":
            await approveClaim(page, fineos_absence_id);
            break;
          case "DENY":
            await denyClaim(page, fineos_absence_id);
            break;
          case "APPROVEDOCS":
            await closeDocuments(page, fineos_absence_id);
            break;
          default:
            throw new Error(
              `Unknown claim.metadata.postSubmit property: ${metadata.postSubmit}`
            );
        }
      });
    }
  };

  // default concurrency of 3 if not specified
  await submit(claimPool, tracker, postSubmit, concurrency || 3);
  await SubmittedClaimIndex.write(
    path.join(storage.dir, "submitted.csv"),
    await ClaimPool.load(storage.claims, storage.documents),
    tracker
  );

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
})().catch((e) => {
  const message = `ERROR: Provide the following arguments - ${chalk.cyan(
    "[directory]"
  )}: ${chalk.italic.green("string")} ${chalk.cyan(
    "[concurrency (optional)]"
  )}: ${chalk.italic.green("number")}`;

  if (e.code !== "ENOENT") console.log(e);
  else console.log(message);
  process.exit(1);
});

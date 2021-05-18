import generateLSTData from "../../scripts/generateLSTData";
import dataDirectory from "../../generation/DataDirectory";
import archiver from "archiver";
import * as fs from "fs";
import path from "path";
import config, { E2ELSTConfig } from "../../config";
import { pipeline, Readable } from "stream";
import { promisify } from "util";
const pipelineP = promisify(pipeline);

export default class Bundler {
  constructor(private floodDirectory: string) {}

  /**
   * Zip up flood files and prepare for upload to Flood.
   *
   * @param outputDirectory
   */
  async bundle(outputDirectory: string): Promise<string[]> {
    const zipFile = path.join(outputDirectory, "archive.zip");

    const output = fs.createWriteStream(
      path.join(outputDirectory, "archive.zip")
    );
    const archive = archiver("zip", {
      zlib: { level: 9 },
    });
    archive.pipe(output);

    archive.directory(this.floodDirectory, false, (entry) => {
      if (entry.name.match(/^data\/documents/) || entry.name.match(/^tmp/)) {
        return false;
      }
      if (entry.name === "index.perf.ts") {
        return false;
      }
      return entry;
    });
    await archive.finalize();

    async function* getIndexFile(sourceFile: string) {
      yield "// @ts-nocheck\n\n";
      yield* fs.createReadStream(sourceFile);
    }

    // Copy in the index file, adding a ts-nocheck header that will prevent missing types from throwing fatal errors.
    const inputIndex = path.join(this.floodDirectory, "index.perf.ts");
    const outputIndex = path.join(outputDirectory, "index.perf.ts");
    await pipelineP(
      Readable.from(getIndexFile(inputIndex)),
      fs.createWriteStream(outputIndex)
    );

    return [zipFile, outputIndex];
  }

  /**
   * Generates scenario data and config JSON.
   *
   * @param scenario
   * @param count
   */
  async generateData(scenario: string, count: number): Promise<void> {
    const storage = dataDirectory("data", this.floodDirectory);
    // Clear and recreate the directory before we generate into it.
    await fs.promises.rmdir(storage.dir, { recursive: true }).catch((e) => {
      if (e.code !== "ENOENT") throw e;
    });
    await storage.prepare();

    const props = [
      "SIMULATION_SPEED",
      "PORTAL_BASEURL",
      "API_BASEURL",
      "FINEOS_BASEURL",
      "FINEOS_USERNAME",
      "FINEOS_PASSWORD",
      "FINEOS_USERS",
      "EMPLOYER_PORTAL_PASSWORD",
      "TESTMAIL_NAMESPACE",
      "TESTMAIL_APIKEY",
    ] as (keyof E2ELSTConfig)[];

    const cfg = props.reduce((cfg, prop) => {
      cfg[`E2E_${prop}`] = config(prop);
      return cfg;
    }, {} as Record<string, string>);
    await fs.promises.writeFile(storage.join("env.json"), JSON.stringify(cfg));

    await generateLSTData(storage, count, scenario);
  }
}

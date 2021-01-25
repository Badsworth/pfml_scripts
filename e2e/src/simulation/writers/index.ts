import { Employer, SimulationClaim } from "../types";
import stream, { pipeline, Transform } from "stream";
import JSONStream from "JSONStream";
import fs from "fs";
import { promisify } from "util";
import transformClaimIndex from "./claimIndex";
import transformDOREmployers from "./DOREmployers";
import {
  transformDOREmployeesEmployerLines,
  transformDOREmployeesWageLines,
} from "./DOREmployees";

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

export async function writeClaimFile(
  claims: AsyncIterable<SimulationClaim>,
  destination: string
): Promise<Record<string, number>> {
  const scenarios: Record<string, number> = {};
  await pipelineP(
    stream.Readable.from(claims, { objectMode: true }),
    new Transform({
      objectMode: true,
      transform(chunk: SimulationClaim, encoding, done) {
        const { scenario } = chunk;
        scenarios[scenario] =
          scenario in scenarios ? scenarios[scenario] + 1 : 1;
        done(null, chunk);
      },
    }),
    JSONStream.stringify(),
    fs.createWriteStream(destination)
  );
  return scenarios;
}

export function writeClaimIndex(
  source: string,
  destination: string
): Promise<void> {
  return pipelineP(
    fs.createReadStream(source),
    JSONStream.parse("*"),
    transformClaimIndex(),
    fs.createWriteStream(destination)
  );
}

type EmployersMap = Map<string, Employer>;

export function writeDOREmployers(
  source: string,
  destination: string,
  employers: EmployersMap
): Promise<void> {
  return pipelineP(
    fs.createReadStream(source),
    JSONStream.parse("*"),
    transformDOREmployers(employers),
    fs.createWriteStream(destination)
  );
}

export async function writeDOREmployees(
  source: string,
  destination: string,
  employers: EmployersMap,
  quarters: Date[]
): Promise<void> {
  await pipelineP(
    fs.createReadStream(source),
    JSONStream.parse("*"),
    transformDOREmployeesEmployerLines(employers, quarters),
    fs.createWriteStream(destination)
  );
  await pipelineP(
    fs.createReadStream(source),
    JSONStream.parse("*"),
    transformDOREmployeesWageLines(employers, quarters),
    fs.createWriteStream(destination, { flags: "a" })
  );
}

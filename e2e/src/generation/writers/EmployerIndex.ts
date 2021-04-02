import { Employer } from "../Employer";
import stringify from "csv-stringify";
import { map } from "streaming-iterables";
import { promisify } from "util";
import { pipeline, Readable } from "stream";
import * as fs from "fs";
const pipelineP = promisify(pipeline);

export default class EmployerIndex {
  static columns = {
    fein: "FEIN",
    name: "Name",
    q1: "2020-03-31 Withholdings",
    q2: "2020-06-30 Withholdings",
    q3: "2020-09-30 Withholdings",
    q4: "2020-12-31 Withholdings",
  };
  static async write(
    employers: Iterable<Employer>,
    filename: string
  ): Promise<void> {
    const buildEmployerLine = ({
      withholdings = [],
      fein,
      name,
    }: Employer): Record<string, string | number> => {
      return {
        fein,
        name,
        q1: withholdings[0],
        q2: withholdings[1],
        q3: withholdings[2],
        q4: withholdings[3],
      };
    };

    await pipelineP(
      Readable.from(map(buildEmployerLine, employers)),
      stringify({ header: true, columns: this.columns }),
      fs.createWriteStream(filename)
    );
  }
}

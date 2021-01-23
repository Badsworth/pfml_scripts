import path from "path";
import { execScript } from "./deployLST";

const command = "bundle";
const desc = "Generates a Flood file bundle";
const builder = {};
const handler = async (): Promise<void> => {
  const bundleDir = path.join(__dirname, "../../../scripts");
  await execScript(
    `cd ${bundleDir} && ${path.join(bundleDir, "makeFloodBundle.sh")}`,
    `Flood bundle was successfully generated in \`${bundleDir}\``
  );
};

export { command, desc, builder, handler };

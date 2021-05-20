import path from "path";
import webpack from "webpack";
import CopyPlugin from "copy-webpack-plugin";
import ZipPlugin from "zip-webpack-plugin";
import dataDirectory from "../../generation/DataDirectory";
import generateLSTData from "../../scripts/generateLSTData";
import { merged } from "../../config";
import winston from "winston";
import * as fs from "fs";

export default class Bundler {
  constructor(private floodDirectory: string, private logger: winston.Logger) {}

  private bundleArchive(outputDirectory: string): Promise<[string, string]> {
    return new Promise((resolve, reject) => {
      const config: webpack.Configuration = {
        context: this.floodDirectory,
        devtool: "cheap-source-map" as const,
        optimization: {
          minimize: false,
          moduleIds: "named",
          usedExports: false,
          providedExports: false,
        },
        entry: {
          "index.perf": `./index.perf.ts`,
        },
        output: {
          path: outputDirectory,
          filename: "[name].[chunkhash].js",
          libraryTarget: "commonjs2",
        },
        mode: "production" as const,
        target: "node",
        // externalsPresets: { node: true }, // Needed for Webpack 5.
        externals: ["@flood/element", "@flood/element-api", "faker"],
        resolve: {
          extensions: [".ts", ".js"],
        },
        module: {
          rules: [
            {
              test: /\.[jt]s$/,
              exclude: [/node_modules/],
              use: [
                {
                  loader: "babel-loader",
                },
              ],
            },
          ],
        },
        plugins: [
          new CopyPlugin({
            patterns: [{ from: `./data/*` }, { from: "./forms/*" }],
          }),
          new ZipPlugin({
            filename: "archive.zip",
          }),
          // Configuration is built into the bundle by string replacing all process.env.E2E_* references
          // in config.ts with their current values.
          new webpack.DefinePlugin(
            Object.fromEntries(
              Object.entries(merged).map(([k, v]) => [
                `process.env.E2E_${k}`,
                JSON.stringify(v),
              ])
            )
          ),
        ],
      };
      webpack(config, (err, stats) => {
        this.logger.debug(stats.toString());
        if (err) return reject(err);
        if (!stats) return reject("Webpack returned nothing");
        if (stats.hasErrors()) return reject(stats.toJson().errors);

        const info = stats.toJson();
        const entrypoints = info.assetsByChunkName?.["index.perf"];
        if (!info.outputPath) return reject("No output path was given");
        if (!entrypoints || !Array.isArray(entrypoints))
          return reject("No chunk was generated for index.perf");
        resolve([path.join(outputDirectory, "archive.zip"), entrypoints[0]]);
      });
    });
  }

  /**
   * Zip up flood files and prepare for upload to Flood.
   *
   * @param outputDirectory
   */
  async bundle(outputDirectory: string): Promise<string[]> {
    // Compile the files using Webpack.
    const [archive, indexJs] = await this.bundleArchive(outputDirectory);

    // Create a .ts file that proxies to our index file within the archive.
    const indexTs = path.join(outputDirectory, "index.ts");
    await fs.promises.writeFile(
      indexTs,
      `// @ts-nocheck\n// This file was auto-generated, and is a stub that proxies to the compiled code.\nimport main, {settings} from "./${indexJs}";\n\nexport default main;\nexport {settings}\n`
    );
    return [archive, indexTs];
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
    await generateLSTData(storage, count, scenario);
  }
}

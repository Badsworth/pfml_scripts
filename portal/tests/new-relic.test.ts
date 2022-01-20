import path from "path";
import { readFileSync } from "fs";

describe("new-relic.js", () => {
  it("does not include Application-specific configuration", () => {
    // Application configuration should be done outside of the snippet. See monitoring.md.
    const data = readFileSync(
      path.resolve(__dirname, "../public/new-relic.js"),
      { encoding: "utf8" }
    );

    expect(data).not.toMatch("window.NREUM.loader_config");
    expect(data).not.toMatch("window.NREUM.info");
  });
});

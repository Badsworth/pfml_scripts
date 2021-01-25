module.exports = {
  options: {
    headless: true,
    devtools: false,
    sandbox: true,
    watch: false,
    stepDelay: 0,
    actionDelay: 0,
    loopCount: 1,
    strict: false,
    failStatusCode: 1,
    verbose: false,
  },
  paths: {
    workRoot: "./src/flood",
    testDataRoot: "./src/flood",
    testPathMatch: ["./src/flood/*.perf.[tj]s", "./src/flood/**/*.perf.[tj]s"],
  },
  flood: {
    hosted: false,
    vu: 1,
    duration: 15,
    rampup: 0,
    regions: ["us-east-1"],
  },
};

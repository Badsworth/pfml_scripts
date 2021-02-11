import * as Util from "./common";
import { factory as EnvFactory } from "../../config";

export default async (
  preset: Util.PresetName,
  env: Util.EnvironmentName
): Promise<void> => {
  const config = EnvFactory(env);
  const floodDefaults: Util.DeployLST = {
    env,
    token: config("FLOOD_API_TOKEN"),
    startAfter: 0,
    startFlood: true,
    name: "Default run",
    threads: 1,
    duration: 15,
    rampup: 0,
    region: "us-east-1",
    tool: "flood-chrome",
    project: "PFML",
    privacy: "public",
    infrastructure: "demand",
    instanceQuantity: 1,
    instanceType: "m5.xlarge",
    stopAfter: 180,
    speed: parseFloat(config("SIMULATION_SPEED") || "0.1"),
    generateData: true,
    numRecords: 100,
    bundleDir: "GHWorkflow",
    scenario: "PortalClaimSubmit",
    chance: 100,
    eligible: 90,
  };
  const floodPresets: Util.Presets = {
    base: [
      {
        ...floodDefaults,
        name: "GHA - Base Preset - PortalClaimSubmit",
        threads: 6,
        bundleDir: "BasePreset",
        scenario: "PortalClaimSubmit",
      },
    ],
    basePlus: [
      {
        ...floodDefaults,
        name: "GHA - BasePlus Preset - PortalClaimSubmit",
        threads: 6,
        duration: 30,
        bundleDir: "BasePlusPreset",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        startAfter: 5,
        name: "GHA - BasePlus Preset - SavilinxAgent",
        threads: 33,
        duration: 15,
        rampup: 3,
        bundleDir: "BasePlus1Preset",
        scenario: "SavilinxAgent",
      },
    ],
    basePlusSpikes: [
      {
        ...floodDefaults,
        name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit",
        threads: 6,
        duration: 60,
        bundleDir: "BasePlusSpikesPreset",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        startAfter: 5, // this flood will start after 5 minutes passed
        name: "GHA - BasePlusSpikes Preset - SavilinxAgent",
        threads: 33,
        duration: 30,
        rampup: 3,
        bundleDir: "BasePlusSpikes1Preset",
        scenario: "SavilinxAgent",
      },
      {
        ...floodDefaults,
        name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit Spike",
        startAfter: 15,
        threads: 20,
        duration: 15,
        bundleDir: "BasePlusSpikes2Preset",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit Spike",
        startAfter: 25,
        threads: 30,
        duration: 15,
        bundleDir: "BasePlusSpikes2Preset",
        scenario: "PortalClaimSubmit",
      },
    ],
  };

  for (const flood of floodPresets[preset]) {
    const floodArgs: string = Object.entries(flood).reduce(
      (allArgs, [k, v]) => `${allArgs} --${k} "${v}"`,
      ""
    );
    // @todo: concerned that github actions will close the script's execution
    // and that some timeouts will not execute.
    setTimeout(
      () =>
        Util.runCommand(`npm run cli -- flood deployLST ${floodArgs}`, true),
      (flood.startAfter || 0) * 60 * 1000
    );
  }
};

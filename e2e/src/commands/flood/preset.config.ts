import * as Util from "./common";
import { factory as EnvFactory } from "../../config";

export default function (env: Util.EnvironmentName): Util.Presets {
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
    numRecords: 500,
    bundleDir: "GHWorkflow",
    scenario: "PortalClaimSubmit",
    chance: 100,
    eligible: 100,
  };
  const floodPresets: Util.Presets = {
    leaveAdmin: [
      {
        ...floodDefaults,
        name: "Leave Admin Registration/Verification",
        threads: 400,
        duration: 60,
        rampup: 30,
        bundleDir: "LeaveAdminSelfRegistration",
        scenario: "LeaveAdminSelfRegistration",
      },
    ],
    base: [
      {
        ...floodDefaults,
        name: "Base Preset - Portal Claims Normal Traffic",
        threads: 6,
        bundleDir: "BasePreset-Normal",
        scenario: "PortalClaimSubmit",
      },
    ],
    basePlus: [
      {
        ...floodDefaults,
        name: "BasePlus Preset - Portal Claims Normal Traffic",
        threads: 6,
        duration: 30,
        bundleDir: "BasePlusPreset-Normal",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        startAfter: 5,
        name: "BasePlus Preset - SavilinxAgent",
        threads: 40,
        duration: 15,
        rampup: 3,
        bundleDir: "BasePlusPreset-Agents",
        scenario: "SavilinxAgent",
      },
    ],
    basePlusSpikes: [
      {
        ...floodDefaults,
        name: "BasePlusSpikes Preset - Portal Claims Normal Traffic",
        threads: 6,
        duration: 60,
        bundleDir: "BasePlusSpikes-Normal",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        startAfter: 5, // this flood will start after 5 minutes passed
        name: "BasePlusSpikes Preset - SavilinxAgent",
        threads: 40,
        duration: 45,
        rampup: 3,
        bundleDir: "BasePlusSpikes-Agents",
        scenario: "SavilinxAgent",
      },
      {
        ...floodDefaults,
        name: "BasePlusSpikes Preset - Portal Claims 1st Spike",
        startAfter: 10,
        threads: 20,
        duration: 15,
        bundleDir: "BasePlusSpikes-1st",
        scenario: "PortalClaimSubmit",
      },
      {
        ...floodDefaults,
        name: "BasePlusSpikes Preset - Portal Claims 2nd Spike",
        startAfter: 23,
        threads: 30,
        duration: 15,
        bundleDir: "BasePlusSpikes-2nd",
        scenario: "PortalClaimSubmit",
      },
    ],
  };
  return floodPresets;
}

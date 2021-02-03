export const presetDefaults = {
  startAfter: 0,
  env: "performance",
  startFlood: true,
  token: null, // needs to come from env variables
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
  speed: 0.1,
  generateData: true,
  numRecords: 100,
  dataOutput: "GHWorkflow",
  scenario: "PortalClaimSubmit",
  chance: 100,
  eligible: 90,
};

export const base = [
  {
    ...presetDefaults,
    name: "GHA - Base Preset - PortalClaimSubmit",
    threads: 6,
    dataOutput: "BasePreset",
    scenario: "PortalClaimSubmit",
  },
];

export const basePlus = [
  {
    ...presetDefaults,
    name: "GHA - BasePlus Preset - PortalClaimSubmit",
    threads: 6,
    duration: 30,
    dataOutput: "BasePlusPreset",
    scenario: "PortalClaimSubmit",
  },
  {
    ...presetDefaults,
    startAfter: 5,
    name: "GHA - BasePlus Preset - SavilinxAgent",
    threads: 33,
    duration: 15,
    rampup: 3,
    dataOutput: "BasePlus1Preset",
    scenario: "SavilinxAgent",
  },
];

export const basePlusSpikes = [
  {
    ...presetDefaults,
    name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit",
    threads: 6,
    duration: 60,
    dataOutput: "BasePlusSpikesPreset",
    scenario: "PortalClaimSubmit",
  },
  {
    ...presetDefaults,
    startAfter: 5, // this flood will start after 5 minutes passed
    name: "GHA - BasePlusSpikes Preset - SavilinxAgent",
    threads: 33,
    duration: 30,
    rampup: 3,
    dataOutput: "BasePlusSpikes1Preset",
    scenario: "SavilinxAgent",
  },
  {
    ...presetDefaults,
    name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit Spike",
    startAfter: 15,
    threads: 20,
    duration: 15,
    dataOutput: "BasePlusSpikes2Preset",
    scenario: "PortalClaimSubmit",
  },
  {
    ...presetDefaults,
    name: "GHA - BasePlusSpikes Preset - PortalClaimSubmit Spike",
    startAfter: 25,
    threads: 30,
    duration: 15,
    dataOutput: "BasePlusSpikes2Preset",
    scenario: "PortalClaimSubmit",
  },
];

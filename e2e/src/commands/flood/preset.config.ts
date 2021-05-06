import { CreateFloodRequest } from "./FloodClient";

export type PresetComponent = {
  // Specification of data to generate.
  data: {
    scenario: string;
    count: number;
  };
  // Flood configuration to use.
  flood: CreateFloodRequest;
  // MS to wait before starting.
  delay?: number;
};
export type Preset = PresetComponent[];

const milliseconds = (minutes: number) => minutes * 60000;
const seconds = (minutes: number) => minutes * 60;

const presets: Record<string, Preset> = {
  leaveAdmin: [
    {
      flood: {
        name: "Leave Admin Registration/Verification",
        project: "PFML",
        duration: seconds(60),
        rampup: seconds(30),
        // We want this to run at a concurrency of 400, and the thread count is *per-instance*, not overall. Each
        // instance is hard capped at 50 threads, so we get to 400 by running 50*8.
        threads: 50,
        grid: {
          instance_quantity: 8,
        },
      },
      data: {
        scenario: "LeaveAdminSelfRegistration",
        count: 500,
      },
    },
  ],
  base: [
    {
      flood: {
        name: "Base Preset - Portal Claims Normal Traffic",
        project: "PFML",
        threads: 6,
        duration: seconds(30),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 500,
      },
    },
  ],
  basePlus: [
    {
      flood: {
        name: "BasePlus Preset - Portal Claims Normal Traffic",
        project: "PFML",
        threads: 6,
        duration: seconds(15),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 500,
      },
    },
    {
      flood: {
        name: "BasePlus Preset - SavilinxAgent",
        project: "PFML",
        threads: 40,
        duration: seconds(15),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 500,
      },
      delay: milliseconds(5),
    },
  ],
  basePlusSpikes: [
    {
      flood: {
        name: "BasePlusSpikes Preset - Portal Claims Normal Traffic",
        project: "PFML",
        threads: 6,
        duration: seconds(60),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 500,
      },
    },
    {
      flood: {
        name: "BasePlusSpikes Preset - SavilinxAgent",
        project: "PFML",
        threads: 40,
        duration: seconds(45),
        rampup: seconds(3),
      },
      data: {
        scenario: "SavilinxAgent",
        count: 500,
      },
      delay: milliseconds(5), // Starts after 5 minutes.
    },
    {
      flood: {
        name: "BasePlusSpikes Preset - Portal Claims 1st Spike",
        project: "PFML",
        threads: 20,
        duration: seconds(15),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 1000,
      },
      delay: milliseconds(10), // 10 minute delay.
    },
    {
      flood: {
        name: "BasePlusSpikes Preset - Portal Claims 2nd Spike",
        project: "PFML",
        threads: 30,
        duration: seconds(15),
      },
      data: {
        scenario: "PortalClaimSubmit",
        count: 1000,
      },
      delay: milliseconds(23), // 23 minute delay.
    },
  ],
};

export default presets;

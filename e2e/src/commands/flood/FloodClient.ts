import FormData from "form-data";
import fetch, { RequestInfo, RequestInit, Response } from "node-fetch";

type FloodGrid = {
  region: "us-east-1";
  infrastructure: "demand";
  instance_quantity: number;
  instance_type: string;
  stop_after: number;
};

type InternalCreateFloodRequest = {
  tool: "flood-chrome";
  project: string;
  name: string;
  privacy_flag: "public" | "private";
  tag_list?: string;
  threads: number;
  rampup?: number;
  duration: number;
  grid?: Partial<FloodGrid>;
};

type Flood = {
  uuid: string;
  status: string;
  name: string;
  permalink: string;
  threads: number;
  rampup: number | null;
  duration: number;
  tag_list: string[];
  created: string;
  started: string;
  stopped: string;
  _embedded: {
    results: {
      name: string;
      href: string;
    }[];
  };
};

const defaults = {
  tool: "flood-chrome" as const,
  privacy_flag: "public" as const,
};

export type CreateFloodRequest = Omit<
  InternalCreateFloodRequest,
  keyof typeof defaults
> &
  Partial<Pick<InternalCreateFloodRequest, keyof typeof defaults>>;

export default class FloodClient {
  constructor(private apiToken: string) {}

  async fetch(url: RequestInfo, init?: RequestInit): Promise<Response> {
    const response = await fetch(url, {
      ...init,
      headers: {
        ...init?.headers,
        Authorization:
          "Basic " + Buffer.from(`${this.apiToken}:`).toString("base64"),
        Accept: "application/vnd.flood.v2+json",
      },
    });
    if (!response.ok) {
      throw new Error(
        `Flood API request failed with a code of ${response.status}(${
          response.statusText
        }): ${await response.text()}`
      );
    }
    return response;
  }

  async getFlood(id: string): Promise<Flood> {
    const response = await this.fetch(`https://api.flood.io/floods/${id}`);
    return response.json();
  }

  async startFlood(
    config: CreateFloodRequest,
    files: NodeJS.ReadableStream[] = []
  ): Promise<Flood> {
    const body = new FormData();
    const { grid, ...requestedConfig } = config;
    for (const [k, v] of Object.entries({ ...defaults, ...requestedConfig })) {
      body.append(`flood[${k}]`, v);
    }

    for (const file of files) {
      body.append("flood_files[]", file);
    }
    const gridDefaults = {
      region: "us-east-1" as const,
      infrastructure: "demand" as const,
      // Default to instance_quantity = 1. A single instance can only run 50 threads (max)
      instance_quantity: 1,
      instance_type: "m5.xlarge",
      // Keep the grid running for 15 minutes longer than the duration of the test.
      stop_after: Math.ceil(config.duration / 60) + 15,
    };

    for (const [k, v] of Object.entries({ ...gridDefaults, ...grid })) {
      body.append(`flood[grids][][${k}]`, v);
    }

    const response = await this.fetch("https://api.flood.io/floods", {
      method: "POST",
      body,
    });
    return response.json();
  }
}

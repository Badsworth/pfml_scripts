import { EventEmitter } from "events";
import { InfluxDB, Point, WriteApi } from "@influxdata/influxdb-client";
import { hostname } from "os";

type ArtilleryStat = {
  min: number;
  max: number;
  median: number;
  p95: number;
  p99: number;
};
type ArtilleryReport = {
  scenariosCreated: number;
  sceanriosCompleted: number;
  requestsCompleted: number;
  latency: ArtilleryStat;
  scenarioDuration: ArtilleryStat;
  rps: { count: number; mean: number };
};
type StatsData = {
  report: () => ArtilleryReport;
  _concurrency: number;
  _generatedScenarios: number;
  _completedScenarios: number;
  _pendingRequests: number;
  _completedRequests: number;
  _scenariosAvoided: number;
  _entries: [
    number, // Timestamp
    string, // uuid
    number, // ?
    number // response code
  ];
  _latencies: number[];
  _errors: {
    [k: string]: number;
  };
  _scenarioCounter: {
    [k: string]: number;
  };
  _counters: {
    [k: string]: number;
  };
  _customStats: {
    [k: string]: number[];
  };
};

type ArtilleryScript = {
  config: {
    plugins: {
      influxdb: {
        url?: string;
        token?: string;
        organization?: string;
        bucket?: string;
      };
    };
  };
};

export class Plugin {
  api: WriteApi;
  pending: Set<Promise<unknown>>;
  constructor(script: ArtilleryScript, events: EventEmitter) {
    const { url, token, organization, bucket } = script.config.plugins.influxdb;
    if (!url || !token || !organization || !bucket) {
      throw new Error("Missing configuration");
    }
    const influx = new InfluxDB({
      url,
      token,
    });
    this.api = influx.getWriteApi(organization, bucket);
    this.api.useDefaultTags({
      run_id: process.env.LST_RUN_ID ?? "Unknown",
      instance_id: process.env.LST_INSTANCE_ID ?? hostname(),
    });
    this.pending = new Set<Promise<unknown>>();
    events.on("stats", this.stats.bind(this));
  }
  stats(data: StatsData): void {
    const report = data.report();
    const point = new Point("artillery")
      .floatField("rps", report.rps.count)
      .intField("concurrency", data._concurrency ?? 0)
      .intField("generatedScenarios", data._generatedScenarios ?? 0)
      .intField("completedScenarios", data._completedScenarios ?? 0)
      .intField("completedRequests", data._completedRequests ?? 0)
      .intField("pendingRequests", data._pendingRequests ?? 0)
      .intField(
        "errors",
        Object.values(data._errors).reduce((i, v) => i + v, 0)
      );

    const responseTime = avg(data._latencies);
    // Guard against NaN values creeping in, which cannot be reported to Influx.
    if (!isNaN(responseTime)) {
      point.floatField("responseTime", responseTime / 1e6);
    }
    // Don't send errors for now. Not sure if the names/length will cause problems on the other side.
    // for(const [name, count] of Object.entries(data._errors)) {
    //   point.intField(`error.${name}`, count);
    // }
    for (const [name, count] of Object.entries(data._scenarioCounter)) {
      point.intField(`completed.${name}`, count);
    }
    for (const [name, count] of Object.entries(data._counters)) {
      point.intField(`counter.${name}`, count);
    }
    for (const [name, points] of Object.entries(data._customStats)) {
      point.floatField(`stat.${name}`, avg(points));
    }
    this.api.writePoint(point);

    // Flush as we go, so data is visible before the test is over.
    this.push(this.api.flush());
  }

  private push(promise: Promise<unknown>) {
    this.pending.add(promise);
    promise.then(() => this.pending.delete(promise));
  }

  async cleanup(done: (err?: Error) => void): Promise<void> {
    try {
      await Promise.all(this.pending);
      await this.api.close();
      done();
    } catch (e) {
      done(e);
    }
  }
}

function avg(points: number[]): number {
  return points.reduce((c, v) => c + v, 0) / points.length;
}

import InfraClient from "../../src/InfraClient";
import config from "../../src/config";
import { subBusinessDays } from "date-fns";
import { ListObjectsV2CommandOutput } from "@aws-sdk/client-s3";
import { describe, beforeAll, expect, it } from "@jest/globals";

/**
 * @group stable
 */
describe("FINEOS extracts", () => {
  let infraClient: InfraClient;
  let extract_objects: ListObjectsV2CommandOutput["Contents"];
  beforeAll(async () => {
    infraClient = InfraClient.create(config);
    extract_objects = await infraClient.getFineosExtracts(
      subBusinessDays(new Date(), 1)
    );
  });

  it("Extracts from the previous day produce an 'OK' file, which confirms data was exported for PFML processing", async () => {
    const okFile = extract_objects.filter(
      (obj) => obj.Key.search(/-OK$/) !== -1
    );
    expect(okFile.length).toBe(1);
  });

  it("Extracts from the previous day contain more then just the 'OK' file", async () => {
    expect(extract_objects.length).toBeGreaterThan(1);
  });
});

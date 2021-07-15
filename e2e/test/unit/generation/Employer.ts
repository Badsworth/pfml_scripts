import { expect, describe, it } from "@jest/globals";
import EmployerPool, { Employer } from "../../../src/generation/Employer";
import { collect } from "streaming-iterables";
import dataDirectory, {
  DataDirectory,
} from "../../../src/generation/DataDirectory";
import * as fs from "fs";

const storage: DataDirectory = dataDirectory("tmp", __dirname);
async function prepareStorage() {
  await storage.prepare();
}
async function removeStorage() {
  await fs.promises.rmdir(storage.dir, { recursive: true });
}

describe("Employer Generation", () => {
  it("generate() should generate an employer pool", () => {
    const pool = EmployerPool.generate(1);
    expect(pool).toBeInstanceOf(EmployerPool);
  });

  it("generate() should generate the requisite amount of properly shaped employers", () => {
    const employers = [...EmployerPool.generate(1)];
    expect(employers).toHaveLength(1);
    expect(employers.pop()).toMatchObject({
      accountKey: expect.stringMatching(/\d{11}/),
      name: expect.any(String),
      fein: expect.stringMatching(/\d{2}\-\d{7}/),
      street: expect.any(String),
      city: expect.any(String),
      state: "MA",
      zip: expect.stringMatching(/\d{5}\-\d{4}/),
      dba: expect.any(String),
      family_exemption: false,
      medical_exemption: false,
      updated_date: expect.any(String),
      size: expect.stringMatching(/(small|medium|large)/),
      metadata: {},
    });
  });

  it("save() and load should properly hydrate and dehydrate() a pool.", async () => {
    const fresh = EmployerPool.generate(1);
    await fresh.save("/tmp/test.txt");
    const reloaded = await EmployerPool.load("/tmp/test.txt");
    expect(reloaded).toEqual(fresh);
  });

  it("Should allow generation of employers of a specific size", () => {
    const pool = EmployerPool.generate(100, { size: "small" });
    for (const employer of pool) {
      expect(employer.size).toEqual("small");
    }
  });

  it("Should allow generation of employers with specific metadata", () => {
    const pool = EmployerPool.generate(1, { metadata: { foo: "bar" } });
    expect(collect(pool)).toContainEqual(
      expect.objectContaining({
        metadata: { foo: "bar" },
      })
    );
  });

  it("Should generate employers according to a size distribution if not given an explicit size", () => {
    const sizes = [...EmployerPool.generate(1000)].reduce(
      (counts, { size = "small" }) => {
        counts[size] += 1;
        return counts;
      },
      { small: 0, medium: 0, large: 0 } as Record<
        NonNullable<Employer["size"]>,
        number
      >
    );
    expect(sizes["small"]).toBeGreaterThan(0);
    expect(sizes["medium"]).toBeGreaterThan(0);
    expect(sizes["large"]).toBeGreaterThan(0);
    expect(sizes["small"]).toBeGreaterThan(sizes["medium"]);
    expect(sizes["medium"]).toBeGreaterThan(sizes["large"]);
  });

  it("pick() should return an employer", () => {
    const employer = EmployerPool.generate(3).pick();
    expect(employer).toHaveProperty("accountKey");
  });

  it("pick() should throw an error if the pool is empty", () => {
    expect(() => EmployerPool.generate(0).pick()).toThrowError(
      "No employers match the specification"
    );
  });

  it("pick() should return larger employers more often than smaller employers", () => {
    const employers = [
      { size: "small" },
      { size: "medium" },
      { size: "large" },
    ] as Employer[];
    const pool = new EmployerPool(employers);
    const distributions = [...Array(100)].map(() => pool.pick().size);
    const counts = distributions.reduce(
      (collected, size) => {
        if (!size) throw new Error("Received an employer without a size");
        collected[size]++;
        return collected;
      },
      { small: 0, medium: 0, large: 0 }
    );
    expect(counts.small).toBeLessThan(counts.medium);
    expect(counts.medium).toBeLessThan(counts.large);
  });

  it("pick() should accept a specification that allows it to match withholdings", () => {
    const employers = [
      { withholdings: [0, 0, 0, 0] },
      { withholdings: [1, 1, 1, 1] },
      { withholdings: [1, 2, 3, 4] },
    ] as Employer[];
    const pool = new EmployerPool(employers);
    expect(pool.pick({ withholdings: "exempt" })).toEqual(employers[0]);
    expect([employers[1], employers[2]]).toContain(
      pool.pick({ withholdings: "non-exempt" })
    );
    expect(pool.pick({ withholdings: [1, 2, 3, 4] })).toEqual(employers[2]);
  });

  it("pick() should accept a specification that allows it to exclude FEINs", () => {
    const employers = [{ fein: "123" }] as Employer[];
    const pool = new EmployerPool(employers);
    expect(() => pool.pick({ notFEIN: "123" })).toThrow(
      "No employers match the specification"
    );
  });

  it("pick() should accept a specification that allows it to pick employers by metadata properties", () => {
    const employers = ([
      { fein: "123", metadata: { foo: "bar" } },
    ] as unknown) as Employer[];
    const pool = new EmployerPool(employers);
    expect(() => pool.pick({ metadata: { foo: "baz" } })).toThrow(
      "No employers match the specification"
    );
    expect(pool.pick({ metadata: { foo: "bar" } })).toMatchObject({
      fein: "123",
    });
  });

  it("generate() should return an employer with quarterly withholding amounts that reflect the employers FEIN", () => {
    const [fresh] = EmployerPool.generate(1);
    for (const withholding of fresh.withholdings) {
      expect(parseInt(fresh.fein.replace("-", "").slice(0, 6)) / 100).toEqual(
        withholding
      );
    }
  });

  it("generate() should return an employer with 4 quarterly withholding amounts of 0 when specified", () => {
    const [fresh] = EmployerPool.generate(1, {
      withholdings: [0, 0, 0, 0],
    });
    for (const withholding of fresh.withholdings) {
      expect(0).toEqual(withholding);
    }
  });

  it("generate() should return an employer with occuring quarterly withholding amounts of 0 at the rate specified", () => {
    const zeroAmount = 1;
    const [fresh] = EmployerPool.generate(1, {
      withholdings: [null, null, null, 0],
    });

    let zeroReceived = 0;
    for (const withholding of fresh.withholdings) {
      if (withholding === 0) zeroReceived += 1;
    }

    expect(zeroAmount).toEqual(zeroReceived);
  });

  it("generate() will set employers quarterly amount to FEIN when withholdings is explicitly undefined", () => {
    const [fresh] = EmployerPool.generate(1, {
      withholdings: undefined,
    });

    for (const withholding of Object.values(fresh.withholdings)) {
      expect(parseInt(fresh.fein.replace("-", "").slice(0, 6)) / 100).toEqual(
        withholding
      );
    }
  });

  describe("andGenerateOrSave", () => {
    beforeEach(async () => {
      await prepareStorage();
    });
    afterEach(async () => {
      await removeStorage();
    });
    it("orGenerateAndSave() will generate used employees when used with load()", async () => {
      const employers = EmployerPool.generate(1);
      const gen = jest.fn(() => employers);
      const pool = await EmployerPool.load(storage.employees).orGenerateAndSave(
        gen
      );
      expect(gen).toHaveBeenCalled();
      expect((await collect(pool)).length).toEqual(
        await collect(await EmployerPool.load(storage.employees)).length
      );
    });
    it("orGenerateAndSave() will save employers to hard drive", async () => {
      await EmployerPool.load(storage.employees).orGenerateAndSave(() =>
        EmployerPool.generate(1)
      );
      const refreshedPool = await EmployerPool.load(storage.employees);
      expect((await collect(refreshedPool)).length).toBe(1);
    });
  });
});

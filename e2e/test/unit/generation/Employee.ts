import { describe, it, expect } from "@jest/globals";
import EmployerPool from "../../../src/generation/Employer";
import EmployeePool, {
  EmployeeGenerator,
  WageSpecification,
} from "../../../src/generation/Employee";
import fs from "fs";
import dataDirectory, {
  DataDirectory,
} from "./../../../src/generation/DataDirectory";
import { collect } from "streaming-iterables";

const storage: DataDirectory = dataDirectory("tmp", __dirname);
const prepareStorage = async () => {
  await storage.prepare();
};
const removeStorage = async () => {
  await fs.promises.rmdir(storage.dir, { recursive: true });
};

const wageTests: [WageSpecification, number, number][] = [
  ["ineligible", 0, 5399],
  ["eligible", 5400, 100000],
  ["high", 90000, 100000],
  ["medium", 30000, 90000],
  ["low", 5400, 30000],
  [10000, 10000, 10000],
];

describe("EmployeeGenerator", () => {
  const employerPool = EmployerPool.generate(1);
  const employer = [...employerPool].pop();

  if (!employer) {
    throw new Error("No employer was generated");
  }

  it("should generate valid employees", () => {
    const employee = EmployeeGenerator.generate(employerPool, {});
    expect(employee).toMatchObject({
      first_name: expect.any(String),
      last_name: expect.any(String),
      ssn: expect.stringMatching(/\d{3}\-\d{2}\-\d{4}/),
      date_of_birth: expect.stringMatching(/\d{4}\-\d{2}\-\d{2}/),
      occupations: expect.arrayContaining([
        expect.objectContaining({
          fein: employer.fein,
          wages: expect.any(Number),
        }),
      ]),
    });
  });

  it("Should generate a birth date 18-65 years in the past.", async () => {
    const employee = EmployeeGenerator.generate(employerPool, {});
    const { date_of_birth } = employee;
    if (typeof date_of_birth !== "string") {
      throw new Error("Expected date_of_birth to be a string");
    }
    const date = new Date(date_of_birth);

    expect(date.getFullYear()).toBeLessThanOrEqual(
      new Date().getFullYear() - 18
    );
    expect(date.getFullYear()).toBeGreaterThanOrEqual(
      new Date().getFullYear() - 65
    );
  });

  it.each(wageTests)(
    "Should be able to generate() an employee with %s wages",
    (wageSpec, min, max) => {
      const employee = EmployeeGenerator.generate(employerPool, {
        wages: wageSpec,
      });
      expect(employee.occupations).toHaveLength(1);
      expect(employee.occupations[0].wages).toBeGreaterThanOrEqual(min);
      expect(employee.occupations[0].wages).toBeLessThanOrEqual(max);
    }
  );
});

describe("EmployeePool", () => {
  afterAll(async () => {
    await fs.promises.rmdir(storage.dir, { recursive: true });
  });

  const employerPool = EmployerPool.generate(1);

  it("generate() should generate an employee pool", () => {
    const pool = EmployeePool.generate(1, employerPool, {});
    expect(pool).toBeInstanceOf(EmployeePool);
  });

  it("generate() should generate valid employees", () => {
    const employees = [...EmployeePool.generate(1, employerPool, {})];
    expect(employees).toHaveLength(1);
  });

  describe("Employee pick()", () => {
    let pool: EmployeePool;
    beforeEach(() => {
      const employees = wageTests.map((spec) => {
        return EmployeeGenerator.generate(employerPool, { wages: spec[0] });
      });
      pool = new EmployeePool(employees);
    });
    beforeAll(async () => await prepareStorage());
    afterAll(async () => await removeStorage());
    it.each(wageTests)(
      "Should be able to pick() an employee with %s wages",
      (spec, min, max) => {
        const employee = pool.pick({
          wages: spec,
        });
        expect(employee.occupations).toHaveLength(1);
        expect(employee.occupations[0].wages).toBeGreaterThanOrEqual(min);
        expect(employee.occupations[0].wages).toBeLessThanOrEqual(max);
      }
    );
    it("Should pick a different employee each time", () => {
      const pool = EmployeePool.generate(10, employerPool, {});
      const ssns = [...new Array(10)]
        .map(() => pool.pick({}))
        .map((e) => e.ssn);
      expect(new Set(ssns).size).toBe(10);
    });

    it("will persist used employees when saved after pick(s) have been performed", async () => {
      const pool = EmployeePool.generate(1, employerPool, {});
      const employee = await pool.pick({});
      await pool.save(storage.employees, storage.usedEmployees);
      const refreshedPool = await EmployeePool.load(
        storage.employees,
        storage.usedEmployees
      );
      expect(refreshedPool.used.size).toBe(1);
      expect(refreshedPool.used.has(employee.ssn)).toBe(true);
    });
  });

  it("pick() should throw an error when there are no employees matching the spec in the pool", () => {
    const pool = EmployeePool.generate(0, employerPool, {
      wages: "high",
    });
    expect(() => pool.pick({ wages: "low" })).toThrowError(
      "No employee is left matching the specification"
    );
  });

  const expectEmployee = expect.objectContaining({
    ssn: expect.any(String),
  });

  it("Can pick employees based on metadata", () => {
    const pool = EmployeePool.generate(1, employerPool, {
      metadata: {
        prenoted: true,
      },
    });
    expect(() => pool.pick({ metadata: { prenoted: false } })).toThrowError(
      "No employee is left matching the specification"
    );
    expect(pool.pick({ metadata: { prenoted: true } })).toEqual(expectEmployee);
  });

  describe("orGenerateAndSave", () => {
    beforeEach(async () => {
      await prepareStorage();
    });
    afterEach(async () => {
      await removeStorage();
    });
    it("orGenerateAndSave() will generate used employees when used with load()", async () => {
      const employees = EmployeePool.generate(1, employerPool, {});
      const gen = jest.fn(() => employees);
      const pool = await EmployeePool.load(storage.employees).orGenerateAndSave(
        gen
      );
      expect(gen).toHaveBeenCalled();
      expect((await collect(pool)).length).toEqual(
        await collect(await EmployeePool.load(storage.employees)).length
      );
    });
    it("orGenerateAndSave() will save employers to hard drive", async () => {
      await EmployeePool.load(storage.employees).orGenerateAndSave(() =>
        EmployeePool.generate(1, employerPool, {})
      );
      const refreshedPool = await EmployeePool.load(storage.employees);
      expect((await collect(refreshedPool)).length).toBe(1);
    });
  });
});

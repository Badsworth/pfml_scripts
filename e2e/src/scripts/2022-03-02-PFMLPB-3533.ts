import { APIClaimSpec } from "../generation/Claim";
import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import { promisify } from "util";
import { pipeline } from "stream";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployerIndex from "../generation/writers/EmployerIndex";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";
import faker from "faker";
import { collect } from "streaming-iterables";
import { ScenarioSpecification } from "generation/Scenario";
import { Phone } from "_api";
import { addDays, addWeeks, subDays } from "date-fns";
import ClaimPool, { APILeaveReason } from "../generation/Claim";

const pipelineP = promisify(pipeline);
(async () => {
  const storage = dataDirectory("2022-03-08-PFMLPB-3533-<env>");
  await storage.prepare();

  const employerPool = await EmployerPool.load(
    storage.employers
  ).orGenerateAndSave(() => EmployerPool.generate(2, { size: "small" }));
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employers.csv")
  );

  const commonFirstNameGroupC = faker.name.firstName();
  const commonLastNameGroupC = faker.name.lastName();
  const commonLastnameGroupE = faker.name.lastName();
  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      // 50 Claimants Clean Claimants (no claims attached) – no Phone #’s (Name search only) -
      EmployeePool.generate(50, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: true, group: "A" },
      }),
      // 50 Claimants with claims & phone #’s
      EmployeePool.generate(60, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: false, group: "B" },
      }),
      // 150 Claimants with same name & no phone number (Name search)
      EmployeePool.generate(160, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: true, group: "C" },
      }),
      // 10 Claimants with same Phone # (with claims attached)
      EmployeePool.generate(15, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: false, group: "D" },
      }),
      // 20 Claimants with the same Phone #, from those 10 would need same last name the other 10 would be different. All with distinct claim #’s
      // same last name
      EmployeePool.generate(12, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: false, group: "E-1" },
      }),
      // different last name
      // 20 Claimants with the same Phone #, from those 10 would need same last name the other 10 would be different. All with distinct claim #’s
      EmployeePool.generate(12, employerPool, {
        mass_id: true,
        wages: "eligible",
        metadata: { clean: false, group: "E-2" },
      })
    )
  );
  await collect(employeePool).forEach((e) => {
    const group = e.metadata?.group as "A" | "B" | "C" | "D" | "E-1" | "E-2";
    if (group === "C") {
      e.first_name = commonFirstNameGroupC;
      e.last_name = commonLastNameGroupC;
    }
    if (group === "E-1") {
      e.last_name = commonLastnameGroupE;
    }
  });

  await employeePool.save(storage.employees);
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );
  await EmployeeIndex.write(
    employeePool,
    path.join(storage.dir, "employees.csv")
  );

  const generatePhoneObj = (phoneNumber: string): Phone => ({
    int_code: "1",
    phone_number: phoneNumber,
    phone_type: "Phone",
  });
  const getRandomLeaveDates = (): [Date, Date] => {
    const randomStartDate = faker.date.between(
      subDays(new Date(), 60),
      addDays(new Date(), 60)
    );
    return [randomStartDate, addWeeks(randomStartDate, 4)];
  };
  const phoneNumberWithoutExtension = () => {
    return (
      "844" +
      "-" +
      faker.random.number({ min: 100, max: 999 }).toString() +
      "-" +
      faker.random.number({ min: 1000, max: 9999 }).toString()
    );
  };
  const groupENumber = generatePhoneObj(phoneNumberWithoutExtension());
  // In adjudication (evidence pending no Documents or Tasks)
  const scenarios: ScenarioSpecification<NonNullable<APIClaimSpec>>[] = [
    {
      employee: { wages: "eligible", metadata: { group: "B" } },
      claim: {
        label: "GROUP_B",
        reason: "Care for a Family Member",
        phone: () => generatePhoneObj(phoneNumberWithoutExtension()),
        leave_dates: getRandomLeaveDates,
        has_continuous_leave_periods: true,
        metadata: {
          leaveDescription: "Random start dates, spanning 4 weeks",
          count: 58,
        },
      },
    },
    {
      employee: { wages: "eligible", metadata: { group: "D" } },
      claim: {
        label: "GROUP_D",
        reason: "Care for a Family Member",
        phone: generatePhoneObj(phoneNumberWithoutExtension()),
        leave_dates: getRandomLeaveDates,
        has_continuous_leave_periods: true,
        metadata: {
          leaveDescription: "Random start dates, spanning 4 weeks",
          count: 13,
        },
      },
    },
    {
      employee: { wages: "eligible", metadata: { group: "E-1" } },
      claim: {
        label: "GROUP_E-1",
        reason: "Care for a Family Member",
        phone: groupENumber,
        leave_dates: getRandomLeaveDates,
        has_continuous_leave_periods: true,
        metadata: {
          leaveDescription: "Random start dates, spanning 4 weeks",
          count: 10,
        },
        docs: {
          MASSID: {},
          CARING: {},
        },
      },
    },
    {
      employee: { wages: "eligible", metadata: { group: "E-2" } },
      claim: {
        label: "GROUP_E-2",
        reason: "Care for a Family Member",
        phone: groupENumber,
        leave_dates: getRandomLeaveDates,
        has_continuous_leave_periods: true,
        metadata: {
          leaveDescription: "Random start dates, spanning 4 weeks",
          count: 10,
        },
      },
    },
  ];

  const scenariosWithRandomLeaveReason = scenarios.map((scenario) => {
    const leaveReasons: readonly NonNullable<APILeaveReason>[] = [
      "Pregnancy/Maternity",
      "Child Bonding",
      "Serious Health Condition - Employee",
      "Care for a Family Member",
    ] as const;

    const selected =
      leaveReasons[Math.floor(Math.random() * leaveReasons.length)];

    const docs: APIClaimSpec["docs"] = {
      MASSID: {},
    };

    if (selected == "Care for a Family Member") {
      docs.CARING = {};
    } else if (selected == "Child Bonding") {
      docs.BIRTHCERTIFICATE = {};
    } else if (selected == "Pregnancy/Maternity") {
      docs.PREGNANCY_MATERNITY_FORM = {};
    } else {
      docs.HCP = {};
    }
    scenario.claim = {
      ...scenario.claim,
      reason: selected,
      reason_qualifier: selected === "Child Bonding" ? "Newborn" : null,
      bondingDate: selected == "Child Bonding" ? "far-past" : undefined,
      docs,
    };

    delete scenario.employee.metadata;
    return scenario;
  });

  await ClaimPool.load(storage.claims, storage.documents).orGenerateAndSave(
    () => {
      return ClaimPool.merge(
        ...scenariosWithRandomLeaveReason.map((scenario) =>
          ClaimPool.generate(
            employeePool,
            scenario.employee,
            scenario.claim,
            scenario.claim.metadata?.count as number
          )
        )
      );
    }
  );

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

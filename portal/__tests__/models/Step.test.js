import Claim from "../../src/models/Claim";
import Step from "../../src/models/Step";
import StepDefinition from "../../src/models/StepDefinition";

describe("Step Model", () => {
  let stepDefinition;
  const name = "step";
  const pages = [
    {
      route: "path/to/page/1",
      fields: ["field_a", "field_b", "field_c"],
    },
    {
      route: "path/to/page/2",
      fields: ["field_d", "field_e"],
    },
  ];

  beforeEach(() => {
    stepDefinition = new StepDefinition({
      name,
      pages,
    });
  });

  describe("href", () => {
    it("returns href with claim id parameter set", () => {
      const step = new Step({
        stepDefinition,
        claim: new Claim({ application_id: "12345" }),
      });

      expect(step.href).toEqual(expect.stringContaining("?claim_id="));
    });
  });

  describe("status", () => {
    describe("when step depends on another step", () => {
      let dependedOnStepDefinition;

      beforeEach(() => {
        dependedOnStepDefinition = new StepDefinition({
          name: "dependedOnStep",
          pages: [
            {
              route: "path/to/page/3",
              fields: ["field_x", "field_y"],
            },
          ],
        });
      });

      describe("when step it depends on has warnings", () => {
        it("returns disabled", () => {
          const warnings = [{ field: "field_y" }];

          const dependedOnStep = new Step({
            stepDefinition: dependedOnStepDefinition,
            claim: {},
            warnings,
          });

          stepDefinition = new StepDefinition({
            name,
            pages,
            dependsOn: [dependedOnStepDefinition],
          });

          const step = new Step({
            stepDefinition,
            claim: {},
            warnings,
            dependsOn: [dependedOnStep],
          });

          expect(step.status).toEqual("disabled");
        });
      });

      describe("when there are no warnings", () => {
        it("returns completed", () => {
          const warnings = [];

          const dependedOnStep = new Step({
            stepDefinition: dependedOnStepDefinition,
            claim: {},
            warnings,
          });

          stepDefinition = new StepDefinition({
            name,
            pages,
            dependsOn: [dependedOnStepDefinition],
          });

          const step = new Step({
            stepDefinition,
            claim: {},
            warnings,
            dependsOn: [dependedOnStep],
          });

          expect(step.status).toEqual("completed");
        });
      });
    });

    describe("when no warnings are returned for fields in step", () => {
      it("returns completed", () => {
        const warnings = [];

        const step = new Step({
          stepDefinition,
          claim: {},
          warnings,
        });

        expect(step.status).toEqual("completed");
      });
    });

    describe("when field has warnings and formState has some fields with values", () => {
      it("returns in_progress", () => {
        const warnings = [{ field: "field_e" }];
        const claim = {
          field_a: null,
          field_b: null,
          field_c: null,
          field_d: null,
          field_e: "value",
        };

        const step = new Step({
          stepDefinition,
          claim,
          warnings,
        });

        expect(step.status).toEqual("in_progress");
      });
    });

    describe("when field has warnings and formState has no fields with values", () => {
      it("returns not_started", () => {
        const warnings = [{ field: "field_e" }];
        const claim = {
          field_a: null,
          field_b: null,
          field_c: null,
          field_d: null,
          field_e: null,
        };

        const step = new Step({
          stepDefinition,
          claim,
          warnings,
        });

        expect(step.status).toEqual("not_started");
      });
    });
  });

  describe("createStepsFromDefinitions", () => {
    let stepDefinitions;
    beforeEach(() => {
      stepDefinitions = ["step1", "step2"].map(
        (name, index) =>
          new StepDefinition({
            name,
            pages: [
              { routes: `path/to/${name}`, fields: [`field_${index + 1}`] },
            ],
          })
      );

      stepDefinitions[1].dependsOn = [stepDefinitions[0]];
    });

    it("creates an array of steps", () => {
      const steps = Step.createStepsFromDefinitions(stepDefinitions, {}, []);

      expect(steps.length).toEqual(2);
      expect(steps[0]).toBeInstanceOf(Step);
      expect(steps[1]).toBeInstanceOf(Step);
    });

    it("add newly created steps to dependsOn array", () => {
      const steps = Step.createStepsFromDefinitions(stepDefinitions, {}, []);

      expect(steps[1].dependsOn[0]).toEqual(steps[0]);
    });

    it("throws error if depended on step does not exist in array", () => {
      const render = () => {
        stepDefinitions[1].dependsOn = [
          new StepDefinition({ name: "stepNotInArray" }),
        ];
        Step.createStepsFromDefinitions(stepDefinitions, {}, []);
      };

      expect(render).toThrowError(/stepNotInArray/);
    });
  });
});

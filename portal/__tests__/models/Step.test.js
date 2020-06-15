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

  describe("status", () => {
    describe("when step it depends on has warnings", () => {
      it("returns disabled", () => {
        const dependedOnStepDefinition = new StepDefinition({
          name: "dependedOnStep",
          pages: [
            {
              route: "path/to/page/3",
              fields: ["field_x", "field_y"],
            },
          ],
        });

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

    describe("when no warnings are returned for fields in step", () => {
      it("returns completed", () => {
        const warnings = [];
        stepDefinition = new StepDefinition({
          name,
          pages,
        });

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

        stepDefinition = new StepDefinition({
          name,
          pages,
        });

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

        stepDefinition = new StepDefinition({
          name,
          pages,
        });

        const step = new Step({
          stepDefinition,
          claim,
          warnings,
        });

        expect(step.status).toEqual("not_started");
      });
    });
  });
});

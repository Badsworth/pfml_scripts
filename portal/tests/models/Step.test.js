import Step, { ClaimSteps } from "../../src/models/Step";
import BaseModel from "../../src/models/BaseModel";
import Claim from "../../src/models/Claim";
import claimantConfig from "../../src/flows/claimant";
import { map } from "lodash";

describe("Step Model", () => {
  const step = "step";
  const pages = [
    {
      step,
      route: "path/to/page/1",
      fields: ["claim.field_a", "claim.field_b", "claim.field_c"],
    },
    {
      step,
      fields: ["claim.field_d", "claim.field_e"],
      nextPage: "path/to/page/1",
    },
  ];

  describe("href", () => {
    it("returns href with claim id parameter set", () => {
      const context = { claim: new Claim({ application_id: "12345" }) };

      const step = new Step({
        name,
        pages,
        context,
      });

      expect(step.href).toEqual(expect.stringContaining("?claim_id="));
    });
  });

  describe("status", () => {
    describe("when step depends on another step", () => {
      describe("when step it depends on has warnings", () => {
        it("returns disabled", () => {
          const warnings = [{ field: "field_y" }];

          const dependedOnStep = new Step({
            name: "dependedOnStep",
            pages: [
              {
                step: "dependedOnStep",
                route: "path/to/page/3",
                fields: ["field_x", "field_y"],
              },
            ],
            context: {},
            warnings,
          });

          const step = new Step({
            name,
            pages,
            context: {},
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
            name: "dependedOnStep",
            pages: [
              {
                route: "path/to/page/3",
                fields: ["field_x", "field_y"],
                nextPage: "path/to/page/1",
              },
            ],
            warnings,
          });

          const step = new Step({
            name,
            pages,
            context: {},
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
          name,
          pages,
          context: {},
          warnings,
        });

        expect(step.status).toEqual("completed");
      });
    });

    describe("when field has warnings and formState has some fields with values", () => {
      it("returns in_progress for field with string value", () => {
        const warnings = [{ field: "claim.field_e" }];
        const claim = {
          field_a: null,
          field_b: null,
          field_c: null,
          field_d: null,
          field_e: "value",
        };

        const step = new Step({
          name,
          pages,
          context: { claim },
          warnings,
        });

        expect(step.status).toEqual("in_progress");
      });

      it("returns in_progress for field with boolean value", () => {
        const warnings = [{ field: "claim.field_e" }];
        const claim = {
          field_a: false,
          field_b: null,
          field_c: null,
          field_d: null,
          field_e: null,
        };

        const step = new Step({
          name,
          pages,
          context: { claim },
          warnings,
        });

        expect(step.status).toEqual("in_progress");
      });

      describe("when a field is a model", () => {
        class TestModel extends BaseModel {
          get defaults() {
            return {
              value: null,
            };
          }
        }

        it("returns not_started when field is the default value", () => {
          const warnings = [{ field: "claim.field_e" }];
          const claim = {
            field_a: null,
            field_b: null,
            field_c: new TestModel(),
            field_d: null,
            field_e: null,
          };

          const step = new Step({
            name,
            pages,
            context: { claim },
            warnings,
          });

          expect(step.status).toEqual("not_started");
        });

        it("returns in_progress when field is not the default value", () => {
          const warnings = [{ field: "claim.field_e" }];
          const claim = {
            field_a: null,
            field_b: null,
            field_c: new TestModel({ value: "Started" }),
            field_d: null,
            field_e: null,
          };

          const step = new Step({
            name,
            pages,
            context: { claim },
            warnings,
          });

          expect(step.status).toEqual("in_progress");
        });
      });
    });

    describe("when field has warnings and formState has no fields with values", () => {
      it("returns not_started", () => {
        const warnings = [{ field: "claim.field_e" }];
        const claim = {
          field_a: null,
          field_b: [],
          field_c: {},
          field_d: null,
          field_e: null,
        };

        const step = new Step({
          name,
          pages,
          context: { claim },
          warnings,
        });

        expect(step.status).toEqual("not_started");
      });
    });
  });

  describe("createClaimSteps", () => {
    it("creates portal steps from machineConfigs", () => {
      const steps = Step.createClaimStepsFromMachine(claimantConfig, {}, []);
      const machinePages = map(claimantConfig.states, (value, key) => ({
        route: key,
        ...value.meta,
      }));

      expect(steps).toHaveLength(7);
      expect(steps.map((s) => s.name)).toEqual(Object.keys(ClaimSteps));
      steps.forEach((s) => {
        expect(s).toBeInstanceOf(Step);
        const expectedPages = machinePages.filter((p) => p.step === s.name);
        expect(Object.values(s.pages || {})).toEqual(
          expect.arrayContaining(expectedPages)
        );
      });
    });
  });
});

import BaseModel from "../../src/models/BaseModel";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import Step from "../../src/models/Step";
import claimantConfig from "../../src/flows/claimant";
import { map } from "lodash";

describe("Step Model", () => {
  const step = "step";
  const pages = [
    {
      route: "path/to/page/1",
      meta: {
        fields: ["claim.field_a", "claim.field_b", "claim.field_c"],
        step,
      },
    },
    {
      route: "path/to/page/2",
      meta: {
        fields: ["claim.field_d", "claim.field_e"],
        step,
      },
    },
  ];

  describe("isComplete", () => {
    it("uses completeCond when present", () => {
      const completeCond = (context) => context.username !== "";
      const sharedStepProps = {
        completeCond,
        pages: [
          {
            route: "/a",
          },
        ],
        warnings: [],
      };

      const incompleteStep = new Step({
        ...sharedStepProps,
        name: "incomplete",
        context: {
          username: "",
        },
      });

      const completedStep = new Step({
        ...sharedStepProps,
        name: "completed",
        context: {
          username: "anton",
        },
      });

      expect(incompleteStep.isComplete).toBe(false);
      expect(completedStep.isComplete).toBe(true);
    });
  });

  describe("isNotApplicable", () => {
    it("returns false without a notApplicableCond", () => {
      const step = new Step();

      expect(step.isNotApplicable).toBe(false);
    });

    it("returns the result of notApplicableCond if one is provided", () => {
      const notApplicableStep = new Step({
        notApplicableCond: () => true,
      });
      const applicableStep = new Step({
        notApplicableCond: () => false,
      });

      expect(notApplicableStep.isNotApplicable).toBe(true);
      expect(applicableStep.isNotApplicable).toBe(false);
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
                route: "path/to/page/3",
                meta: {
                  fields: ["field_x", "field_y"],
                  step: "dependedOnStep",
                },
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
                meta: {
                  fields: ["field_x", "field_y"],
                },
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

    describe("when field has warnings and claim fields aren't empty", () => {
      it("returns in_progress when Step has field with string value", () => {
        const warnings = [{ field: "field_e" }];
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
        const warnings = [{ field: "field_e" }];
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

      it("returns in_progress for field with number value", () => {
        const warnings = [{ field: "field_e" }];
        const claim = {
          field_a: 4,
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
          const warnings = [{ field: "field_e" }];
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
          const warnings = [{ field: "field_e" }];
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

    describe("when field is a number", () => {
      it("returns completed", () => {
        const warnings = [];
        const claim = {
          field_e: 0,
        };

        const step = new Step({
          name,
          pages,
          context: { claim },
          warnings,
        });

        expect(step.status).toEqual("completed");
      });
    });

    describe("when field has warnings and formState has no fields with values", () => {
      it("returns not_started", () => {
        const warnings = [{ field: "field_e" }];
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
    it("creates expected portal steps from machineConfigs", () => {
      const steps = Step.createClaimStepsFromMachine(
        claimantConfig,
        { claim: new MockBenefitsApplicationBuilder().create() },
        []
      );

      expect(steps.map((s) => s.name)).toMatchInlineSnapshot(`
Array [
  "VERIFY_ID",
  "EMPLOYER_INFORMATION",
  "LEAVE_DETAILS",
  "OTHER_LEAVE",
  "REVIEW_AND_CONFIRM",
  "PAYMENT",
  "UPLOAD_ID",
  "UPLOAD_CERTIFICATION",
]
`);
    });

    it("sets #pages property for each Step", () => {
      const steps = Step.createClaimStepsFromMachine(
        claimantConfig,
        { claim: new MockBenefitsApplicationBuilder().create() },
        []
      );
      const machinePages = map(claimantConfig.states, (value, key) => ({
        route: key,
        meta: value.meta,
      }));

      steps.forEach((s) => {
        expect(s).toBeInstanceOf(Step);
        const expectedPages = machinePages.filter((p) => p.step === s.name);
        expect(Object.values(s.pages || {})).toEqual(
          expect.arrayContaining(expectedPages)
        );
      });
    });

    it("marks group 1 steps as uneditable when Claim is submitted", () => {
      const steps = Step.createClaimStepsFromMachine(
        claimantConfig,
        { claim: new MockBenefitsApplicationBuilder().submitted().create() },
        []
      );

      steps.forEach((step) => {
        const expectedEditableValue = step.group !== 1;
        expect(step.editable).toBe(expectedEditableValue);
      });
    });

    it("marks group 2 steps as uneditable when payment is submitted", () => {
      const steps = Step.createClaimStepsFromMachine(
        claimantConfig,
        {
          claim: new MockBenefitsApplicationBuilder()
            .paymentPrefSubmitted()
            .create(),
        },
        []
      );

      steps.forEach((step) => {
        const expectedEditableValue = step.group === 3;
        expect(step.editable).toBe(expectedEditableValue);
      });
    });
  });
});

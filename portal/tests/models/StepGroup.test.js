import Step from "../../src/models/Step";
import StepGroup from "../../src/models/StepGroup";

describe("StepGroup", () => {
  describe("#isEnabled", () => {
    it("returns true when at least one step is not disabled", () => {
      const warnings = [{ field: "field_y" }];

      const dependsOn = [
        new Step({
          name: "dependedOnStep",
          pages: [
            {
              route: "path/to/page/3",
              meta: {
                step: "dependedOnStep",
                fields: ["field_x", "field_y"],
              },
            },
          ],
          context: {},
          warnings,
        }),
      ];

      const steps = [
        new Step({
          name: "A",
        }),
        new Step({
          name: "B",
          dependsOn,
        }),
      ];

      const group = new StepGroup({
        number: 2,
        steps,
      });

      expect(group.isEnabled).toBe(true);
    });

    it("returns false when all steps are disabled", () => {
      const warnings = [{ field: "field_y" }];

      const dependsOn = [
        new Step({
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
        }),
      ];

      const steps = [
        new Step({
          name: "A",
          dependsOn,
        }),
        new Step({
          name: "B",
          dependsOn,
        }),
      ];

      const group = new StepGroup({
        number: 2,
        steps,
      });

      expect(group.isEnabled).toBe(false);
    });
  });
});

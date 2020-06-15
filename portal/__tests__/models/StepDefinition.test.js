import StepDefinition from "../../src/models/StepDefinition";

describe("Step Model", () => {
  let stepDef;
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
    stepDef = new StepDefinition({
      name,
      pages,
    });
  });

  describe("fields", () => {
    it("flattens step fields", () => {
      expect(stepDef.fields).toEqual([
        "field_a",
        "field_b",
        "field_c",
        "field_d",
        "field_e",
      ]);
    });
  });

  describe("initialPage", () => {
    it("gets route for first page", () => {
      expect(stepDef.initialPage).toEqual("path/to/page/1");
    });
  });
});

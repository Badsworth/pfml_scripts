import Duration from "../../../src/pages/claims/duration";
import { renderWithAppLogic } from "../../test-utils";

describe("Duration", () => {
  describe("regardless of duration type", () => {
    it("initially renders the page without conditional fields", () => {
      const { wrapper } = renderWithAppLogic(Duration);

      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });
  });

  describe("when user indicates that leave is continuous", () => {
    it("doesn't render conditional fields", () => {
      const { wrapper } = renderWithAppLogic(Duration, {
        claimAttrs: { duration_type: "continuous" },
      });

      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });
  });

  describe("when user indicates that leave is intermittent", () => {
    it("renders conditional field", () => {
      const { wrapper } = renderWithAppLogic(Duration, {
        claimAttrs: { duration_type: "intermittent" },
      });

      expect(wrapper.find("ConditionalContent").prop("visible")).toBeTruthy();
    });
  });
});

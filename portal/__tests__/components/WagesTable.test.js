import React from "react";
import WagesTable from "../../src/components/WagesTable";
import i18next from "i18next";

import { mount } from "enzyme";

describe("WagesTable", () => {
  describe("when employee is ineligible", () => {
    it("renders WagesTable component with intro text for someone who is ineligible", () => {
      // mounting because table isn't rendered until after result of useEffect
      const wrapper = mount(
        <WagesTable eligibility="ineligible" employeeId="1234" />
      );

      expect(wrapper.find("Lead").text()).toEqual(
        i18next.t("components.wagesTable.ineligibleDescription")
      );
    });
  });

  describe("when employee is eligible", () => {
    it("renders WagesTable component with intro text for someone who is eligible", () => {
      // mounting because table isn't rendered until after result of useEffect
      const wrapper = mount(
        <WagesTable eligibility="eligible" employeeId="1234" />
      );
      expect(
        wrapper
          .find("Lead")
          .at(1)
          .text()
      ).toEqual(i18next.t("components.wagesTable.eligibleDescriptionP2"));
    });
  });
});

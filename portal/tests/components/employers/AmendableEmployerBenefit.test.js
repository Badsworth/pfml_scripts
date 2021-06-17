import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("AmendableEmployerBenefit", () => {
  const shortTermDisability = new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_amount_frequency: EmployerBenefitFrequency.monthly,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: 0,
  });
  const onChange = jest.fn();
  const onRemove = jest.fn();
  const employerBenefit = shortTermDisability;

  let appLogic, wrapper;

  const v2ExclusiveFields = ["benefit_type", "is_full_salary_continuous"];

  it("does not show v2 exclusive fields in v1", () => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin={false}
        employerBenefit={employerBenefit}
        onChange={onChange}
        onRemove={onRemove}
        shouldShowV2={false}
      />
    );

    for (const field of v2ExclusiveFields) {
      expect(
        wrapper.find(`[name="employer_benefits[0].${field}"]`).exists()
      ).toBe(true);
    }
  });

  it("shows v2-exclusive fields in v2", () => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin={false}
        employerBenefit={employerBenefit}
        onChange={onChange}
        onRemove={onRemove}
        shouldShowV2
      />
    );

    for (const field of v2ExclusiveFields) {
      expect(
        wrapper.find(`[name="employer_benefits[0].${field}"]`).exists()
      ).toBe(true);
    }
  });

  describe("for amended benefits", () => {
    function clickAmendButton(wrapper) {
      wrapper
        .find("BenefitDetailsRow")
        .dive()
        .find("AmendButton")
        .simulate("click");
    }

    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(
        <AmendableEmployerBenefit
          appErrors={appLogic.appErrors}
          isAddedByLeaveAdmin={false}
          employerBenefit={employerBenefit}
          onChange={onChange}
          onRemove={onRemove}
          shouldShowV2
        />
      );
    });

    it("renders the component with a table row for existing data", () => {
      expect(wrapper.find("BenefitDetailsRow").exists()).toBe(true);
      expect(wrapper).toMatchSnapshot();
    });

    it("renders formatted date range for benefit used by employee", () => {
      expect(
        wrapper.find("BenefitDetailsRow").dive().find("th").text()
      ).toEqual("2/1/2021 – 3/1/2021");
    });

    it("renders formatted benefit type as sentence case", () => {
      expect(
        wrapper.find("BenefitDetailsRow").dive().find("td").first().text()
      ).toEqual("Short-term disability insurance");
    });

    it("renders formatted benefit amount with dollar sign and frequency", () => {
      expect(
        wrapper.find("BenefitDetailsRow").dive().find("td").at(1).text()
      ).toEqual("$1,000.00 per month");
    });

    it("renders information about unknown frequency when frequency is 'Unknown'", () => {
      const paidLeave = new EmployerBenefit({
        benefit_amount_dollars: 0,
        benefit_amount_frequency: "Unknown",
        benefit_end_date: "2021-03-01",
        benefit_start_date: "2021-02-01",
        benefit_type: EmployerBenefitType.paidLeave,
        employer_benefit_id: 0,
      });
      const wrapper = shallow(
        <AmendableEmployerBenefit
          appErrors={appLogic.appErrors}
          isAddedByLeaveAdmin={false}
          employerBenefit={paidLeave}
          onChange={onChange}
          onRemove={onRemove}
          shouldShowV2
        />
      );

      expect(
        wrapper.find("BenefitDetailsRow").dive().find("td").at(1).text()
      ).toEqual("$0.00 (frequency unknown)");
    });

    it("renders an AmendmentForm if user clicks on AmendButton", () => {
      clickAmendButton(wrapper);

      expect(wrapper.find("AmendmentForm").exists()).toEqual(true);
    });

    it("updates start and end dates in the AmendmentForm", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "2020-10-10" } });
      wrapper
        .find("InputDate")
        .last()
        .simulate("change", { target: { value: "2020-10-20" } });

      expect(onChange).toHaveBeenCalledTimes(2);
      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-10-10"
      );
      expect(wrapper.find("InputDate").last().prop("value")).toEqual(
        "2020-10-20"
      );
    });

    it("updates amount in the AmendmentForm", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputCurrency")
        .simulate("change", { target: { value: 500 } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "amendedBenefits"
      );
      expect(wrapper.find("InputCurrency").prop("value")).toEqual(500);
    });

    it("formats empty dates to null instead of an empty string", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "" } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_start_date: null }),
        "amendedBenefits"
      );
    });

    it("updates frequency in the AmendmentForm", () => {
      clickAmendButton(wrapper);
      wrapper.find("Dropdown").simulate("change", {
        target: { value: EmployerBenefitFrequency.weekly },
      });

      expect(onChange).toHaveBeenCalled();
      expect(wrapper.find("Dropdown").prop("value")).toEqual(
        EmployerBenefitFrequency.weekly
      );
    });

    it("restores original value on cancel", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputCurrency")
        .simulate("change", { target: { value: 500 } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "amendedBenefits"
      );
      expect(wrapper.find("InputCurrency").prop("value")).toEqual(500);

      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");

      clickAmendButton(wrapper);
      expect(wrapper.find("InputCurrency").prop("value")).toEqual(1000);
    });
  });

  describe("for added benefits", () => {
    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(
        <AmendableEmployerBenefit
          appErrors={appLogic.appErrors}
          isAddedByLeaveAdmin
          employerBenefit={employerBenefit}
          onChange={onChange}
          onRemove={onRemove}
          shouldShowV2
        />
      );
    });

    it("renders the component without a table row", () => {
      expect(wrapper.find("BenefitDetailsRow").exists()).toBe(false);
      expect(wrapper).toMatchSnapshot();
    });

    it("updates start and end dates in the AmendmentForm", () => {
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "2020-10-10" } });
      wrapper
        .find("InputDate")
        .last()
        .simulate("change", { target: { value: "2020-10-20" } });

      expect(onChange).toHaveBeenCalledTimes(2);
      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-10-10"
      );
      expect(wrapper.find("InputDate").last().prop("value")).toEqual(
        "2020-10-20"
      );
    });

    it("updates amount in the AmendmentForm", () => {
      wrapper
        .find("InputCurrency")
        .simulate("change", { target: { value: 500 } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "addedBenefits"
      );
      expect(wrapper.find("InputCurrency").prop("value")).toEqual(500);
    });

    it("formats empty dates to null instead of an empty string", () => {
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "" } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_start_date: null }),
        "addedBenefits"
      );
    });

    it("updates frequency in the AmendmentForm", () => {
      wrapper.find("Dropdown").simulate("change", {
        target: { value: EmployerBenefitFrequency.weekly },
      });

      expect(onChange).toHaveBeenCalled();
      expect(wrapper.find("Dropdown").prop("value")).toEqual(
        EmployerBenefitFrequency.weekly
      );
    });

    it("calls 'onRemove' on cancel", () => {
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");
      expect(onRemove).toHaveBeenCalled();
    });
  });
});

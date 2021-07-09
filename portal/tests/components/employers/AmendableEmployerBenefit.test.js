import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { simulateEvents, testHook } from "../../test-utils";
import AmendableEmployerBenefit from "../../../src/components/employers/AmendableEmployerBenefit";
import React from "react";
import { shallow } from "enzyme";
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

  // data-test props of fields that should not be seen in v1.
  const v2ExclusiveFields = [
    "benefit-type-input",
    "is-full-salary-continuous-input",
  ];

  // traverse up through the DOM and make sure all ConditionalContents have visible === true
  function isElementVisible(element) {
    const conditionalContentParents = element.parents("ConditionalContent");
    if (
      conditionalContentParents.someWhere((el) => el.prop("visible") === false)
    ) {
      return false;
    }
    return true;
  }

  it("does not show v2 exclusive fields in v1", () => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin
        employerBenefit={employerBenefit}
        onChange={onChange}
        onRemove={onRemove}
        shouldShowV2={false}
      />
    );

    for (const field of v2ExclusiveFields) {
      const element = wrapper.find({ "data-test": field });
      expect(isElementVisible(element)).toBe(false);
    }
  });

  it("shows v2-exclusive fields in v2", () => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    const wrapper = shallow(
      <AmendableEmployerBenefit
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin
        employerBenefit={employerBenefit}
        onChange={onChange}
        onRemove={onRemove}
        shouldShowV2
      />
    );

    for (const field of v2ExclusiveFields) {
      const element = wrapper.find({ "data-test": field });
      expect(isElementVisible(element)).toBe(true);
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

    it("renders the component with a table row for existing data and with the amendment form hidden", () => {
      expect(wrapper.find("BenefitDetailsRow").exists()).toBe(true);
      expect(
        wrapper
          .find("AmendmentForm")
          .closest("ConditionalContent")
          .prop("visible")
      ).toBe(false);
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

    it("renders amountPerFrequency_unknown when amount not zero AND frequency is 'Unknown'", () => {
      const paidLeave = new EmployerBenefit({
        benefit_amount_dollars: 200,
        benefit_amount_frequency: EmployerBenefitFrequency.unknown,
        benefit_end_date: "2021-03-01",
        benefit_start_date: "2021-02-01",
        benefit_type: EmployerBenefitType.paidLeave,
        employer_benefit_id: 0,
        is_full_salary_continuous: false,
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
      ).toEqual("$200.00 (frequency unknown)");
    });

    it("renders fullSalaryContinuous when is_full_salary_continuous is true", () => {
      const fullSalaryContinuousPaidLeave = new EmployerBenefit({
        benefit_amount_dollars: 0,
        benefit_amount_frequency: EmployerBenefitFrequency.unknown,
        benefit_end_date: "2021-03-01",
        benefit_start_date: "2021-02-01",
        benefit_type: EmployerBenefitType.paidLeave,
        employer_benefit_id: 0,
        is_full_salary_continuous: true,
      });
      const wrapper = shallow(
        <AmendableEmployerBenefit
          appErrors={appLogic.appErrors}
          isAddedByLeaveAdmin={false}
          employerBenefit={fullSalaryContinuousPaidLeave}
          onChange={onChange}
          onRemove={onRemove}
          shouldShowV2
        />
      );

      expect(
        wrapper.find("BenefitDetailsRow").dive().find("td").at(1).text()
      ).toEqual("Full salary continuous");
    });

    it("renders noAmountReported when benefit_amount_dollars is 0.00 AND benefit_amount_frequency is unknown AND is_full_salary_continuous is falsy", () => {
      const noAmountNoFreqPaidLeave = new EmployerBenefit({
        benefit_amount_dollars: 0,
        benefit_amount_frequency: EmployerBenefitFrequency.unknown,
        benefit_end_date: "2021-03-01",
        benefit_start_date: "2021-02-01",
        benefit_type: EmployerBenefitType.paidLeave,
        employer_benefit_id: 0,
        is_full_salary_continuous: false,
      });
      const wrapper = shallow(
        <AmendableEmployerBenefit
          appErrors={appLogic.appErrors}
          isAddedByLeaveAdmin={false}
          employerBenefit={noAmountNoFreqPaidLeave}
          onChange={onChange}
          onRemove={onRemove}
          shouldShowV2
        />
      );

      expect(
        wrapper.find("BenefitDetailsRow").dive().find("td").at(1).text()
      ).toEqual("No amount reported");
    });

    it("renders an AmendmentForm if user clicks on AmendButton", () => {
      clickAmendButton(wrapper);

      expect(
        wrapper
          .find("AmendmentForm")
          .closest("ConditionalContent")
          .prop("visible")
      ).toBe(true);
    });

    it("updates start and end dates in the AmendmentForm", () => {
      clickAmendButton(wrapper);

      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_start_date", "2020-10-10");
      changeField("employer_benefits[0].benefit_end_date", "2020-10-20");

      expect(onChange).toHaveBeenCalledTimes(2);
      expect(
        wrapper.find({ "data-test": "benefit-start-date-input" }).prop("value")
      ).toEqual("2020-10-10");
      expect(
        wrapper.find({ "data-test": "benefit-end-date-input" }).prop("value")
      ).toEqual("2020-10-20");
    });

    it("updates amount in the AmendmentForm", () => {
      clickAmendButton(wrapper);

      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_amount_dollars", 500);

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "amendedBenefits"
      );
      expect(
        wrapper
          .find({ "data-test": "benefit-amount-dollars-input" })
          .prop("value")
      ).toEqual(500);
    });

    it("formats empty dates to null instead of an empty string", () => {
      clickAmendButton(wrapper);

      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_start_date", "");

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_start_date: null }),
        "amendedBenefits"
      );
    });

    it("updates frequency in the AmendmentForm", () => {
      clickAmendButton(wrapper);

      const { changeRadioGroup } = simulateEvents(wrapper);
      changeRadioGroup(
        "employer_benefits[0].benefit_amount_frequency",
        EmployerBenefitFrequency.weekly
      );

      expect(onChange).toHaveBeenCalledWith(
        {
          benefit_amount_frequency: EmployerBenefitFrequency.weekly,
          employer_benefit_id: 0,
        },
        "amendedBenefits"
      );
      expect(
        wrapper
          .find({ "data-test": "benefit-amount-frequency-input" })
          .prop("value")
      ).toEqual(EmployerBenefitFrequency.weekly);
    });

    it("restores original value on cancel", () => {
      clickAmendButton(wrapper);

      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_amount_dollars", 500);
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "amendedBenefits"
      );
      expect(
        wrapper
          .find({ "data-test": "benefit-amount-dollars-input" })
          .prop("value")
      ).toEqual(500);

      wrapper
        .find("AmendmentForm")
        .dive()
        .find({ "data-test": "amendment-destroy-button" })
        .simulate("click");

      expect(
        wrapper
          .find({ "data-test": "benefit-amount-dollars-input" })
          .prop("value")
      ).toEqual(1000);
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

    it("renders the component without a table row and with a visible amendment form", () => {
      expect(wrapper.find("BenefitDetailsRow").exists()).toBe(false);
      expect(
        wrapper
          .find("AmendmentForm")
          .closest("ConditionalContent")
          .prop("visible")
      ).toBe(true);
      expect(wrapper).toMatchSnapshot();
    });

    it("updates start and end dates in the AmendmentForm", () => {
      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_start_date", "2020-10-10");
      changeField("employer_benefits[0].benefit_end_date", "2020-10-20");

      expect(onChange).toHaveBeenCalledTimes(2);
      expect(
        wrapper.find({ "data-test": "benefit-start-date-input" }).prop("value")
      ).toEqual("2020-10-10");
      expect(
        wrapper.find({ "data-test": "benefit-end-date-input" }).prop("value")
      ).toEqual("2020-10-20");
    });

    it("updates amount in the AmendmentForm", () => {
      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_amount_dollars", 500);

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_amount_dollars: 500 }),
        "addedBenefits"
      );
      expect(
        wrapper
          .find({ "data-test": "benefit-amount-dollars-input" })
          .prop("value")
      ).toEqual(500);
    });

    it("formats empty dates to null instead of an empty string", () => {
      const { changeField } = simulateEvents(wrapper);
      changeField("employer_benefits[0].benefit_start_date", "");

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ benefit_start_date: null }),
        "addedBenefits"
      );
    });

    it("updates frequency in the AmendmentForm", () => {
      const { changeRadioGroup } = simulateEvents(wrapper);
      changeRadioGroup(
        "employer_benefits[0].benefit_amount_frequency",
        EmployerBenefitFrequency.weekly
      );

      expect(onChange).toHaveBeenCalledWith(
        {
          benefit_amount_frequency: EmployerBenefitFrequency.weekly,
          employer_benefit_id: 0,
        },
        "addedBenefits"
      );
      expect(
        wrapper
          .find({ "data-test": "benefit-amount-frequency-input" })
          .prop("value")
      ).toEqual(EmployerBenefitFrequency.weekly);
    });

    it("calls 'onRemove' on cancel", () => {
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");
      expect(onRemove).toHaveBeenCalled();
    });
  });
});

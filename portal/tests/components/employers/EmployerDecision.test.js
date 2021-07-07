import { mount, shallow } from "enzyme";
import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import EmployerDecision from "../../../src/components/employers/EmployerDecision";
import React from "react";
import { act } from "react-dom/test-utils";
import { merge } from "lodash";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("EmployerDecision", () => {
  const updateFields = jest.fn().mockImplementation((arg) => {
    if (arg.employer_decision) {
    }
  });
  let getFunctionalInputProps;

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: { employerDecision: "Approve" },
        updateFields,
      });
    });
  });

  function render(shouldMount = false, customProps = {}) {
    const defaultProps = {
      employerDecision: undefined,
      fraud: undefined,
      getFunctionalInputProps,
      updateFields,
    };
    const props = merge(defaultProps, customProps);
    if (shouldMount) {
      return mount(<EmployerDecision {...props} />);
    } else {
      return shallow(<EmployerDecision {...props} />);
    }
  }

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("updates the form state on change", () => {
    const wrapper = render();
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("employer_decision", "Approve");
    changeRadioGroup("employer_decision", "Deny");

    expect(updateFields).toHaveBeenCalledTimes(2);
    expect(updateFields).toHaveBeenNthCalledWith(1, {
      employer_decision: "Approve",
    });
    expect(updateFields).toHaveBeenNthCalledWith(2, {
      employer_decision: "Deny",
    });
  });

  describe("when fraud is 'Yes'", () => {
    it('disables the "Approve" option and selects "Deny"', () => {
      const wrapper = render(true, { fraud: "Yes" });
      expect(updateFields).toHaveBeenCalledWith({ employer_decision: "Deny" });
      // simulate updateFields, which was tested above.
      act(() => {
        wrapper.setProps({ employerDecision: "Deny" });
      });
      wrapper.update();

      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const approveOption = choices.find(
        (choice) => choice.value === "Approve"
      );
      const denyOption = choices.find((choice) => choice.value === "Deny");

      expect(approveOption.disabled).toBe(true);
      expect(denyOption.checked).toBe(true);
    });

    describe("and is changed to 'No'", () => {
      it('re-enables the "Approve" option', () => {
        const wrapper = render(true, { fraud: "Yes" });
        act(() => {
          wrapper.setProps({ fraud: "No" });
        });
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const approveOption = choices.find(
          (choice) => choice.value === "Approve"
        );

        expect(approveOption.disabled).toBe(false);
      });

      it("clears the selection", () => {
        const wrapper = render(true, { fraud: "Yes" });
        act(() => {
          wrapper.setProps({ fraud: "No" });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        for (const choice of choices) {
          expect(choice.checked).toBe(false);
        }
      });
    });
  });
});

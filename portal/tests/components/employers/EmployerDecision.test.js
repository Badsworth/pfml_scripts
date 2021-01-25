import { mount, shallow } from "enzyme";
import EmployerDecision from "../../../src/components/employers/EmployerDecision";
import React from "react";
import { act } from "react-dom/test-utils";
import { simulateEvents } from "../../test-utils";

describe("EmployerDecision", () => {
  let wrapper;
  const onChange = jest.fn();

  beforeEach(() => {
    wrapper = shallow(<EmployerDecision fraud="No" onChange={onChange} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("calls 'onChange' when the decision has changed", () => {
    wrapper = mount(<EmployerDecision fraud="No" onChange={onChange} />);
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("employerDecision", "Approve");
    changeRadioGroup("employerDecision", "Deny");

    expect(onChange).toHaveBeenCalledTimes(3);
    // first call is on mount
    expect(onChange).toHaveBeenNthCalledWith(1, undefined);
    expect(onChange).toHaveBeenNthCalledWith(2, "Approve");
    expect(onChange).toHaveBeenNthCalledWith(3, "Deny");
  });

  describe("when fraud is true", () => {
    beforeEach(() => {
      wrapper = mount(<EmployerDecision fraud="Yes" onChange={onChange} />);
    });

    it('disables the "Approve" option and selects "Deny"', () => {
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const approveOption = choices.find(
        (choice) => choice.value === "Approve"
      );
      const denyOption = choices.find((choice) => choice.value === "Deny");

      expect(approveOption.disabled).toBe(true);
      expect(denyOption.checked).toBe(true);
    });

    describe("and is changed to 'No'", () => {
      beforeEach(() => {
        act(() => {
          wrapper.setProps({ fraud: "No" });
        });
        // for useEffect to take place
        wrapper.update();
      });

      it('re-enables the "Approve" option', () => {
        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const approveOption = choices.find(
          (choice) => choice.value === "Approve"
        );
        expect(approveOption.disabled).toBe(false);
      });

      it("clears the selection", () => {
        const choices = wrapper.find("InputChoiceGroup").prop("choices");

        for (const choice of choices) {
          expect(choice.checked).toBe(false);
        }
      });
    });
  });
});

import { mount, shallow } from "enzyme";
import Feedback from "../../../src/components/employers/Feedback";
import FileCardList from "../../../src/components/FileCardList";
import React from "react";
import { act } from "react-dom/test-utils";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const appLogic = useAppLogic();
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<Feedback appLogic={appLogic} onSubmit={() => {}} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when employerDecision is 'Deny'", () => {
    beforeEach(() => {
      wrapper = shallow(
        <Feedback
          appLogic={appLogic}
          employerDecision="Deny"
          onSubmit={() => {}}
        />
      );
    });

    it("disables the 'No' option and selects 'Yes'", () => {
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    describe("and is changed to 'Approve'", () => {
      beforeEach(() => {
        wrapper = mount(
          <Feedback
            appLogic={appLogic}
            employerDecision="Deny"
            onSubmit={() => {}}
          />
        );
      });

      it('re-enables the "No" option', () => {
        act(() => {
          wrapper.setProps({ employerDecision: "Approve" });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.disabled).toBe(false);
      });

      it('selects the "No" option if there is no comment typed', () => {
        act(() => {
          wrapper.setProps({ employerDecision: "Approve" });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.checked).toBe(true);
      });

      it('keeps "Yes" selected if there is a comment typed', () => {
        const { changeField } = simulateEvents(wrapper);
        changeField("comment", "some comment");

        act(() => {
          wrapper.setProps({ employerDecision: "Approve" });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const yesOption = choices.find((choice) => choice.label === "Yes");
        expect(yesOption.checked).toBe(true);
      });
    });
  });

  describe("when employerDecision is 'Approve'", () => {
    it("no options are disabled", () => {
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBeFalsy();
      expect(yesOption.disabled).toBeFalsy();
    });
  });

  describe("when user selects option to leave additional comments", () => {
    it("shows comment box and file upload button", () => {
      const { changeRadioGroup } = simulateEvents(wrapper);
      changeRadioGroup("hasComment", "true");

      expect(wrapper.find("textarea").exists()).toEqual(true);
      expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });
});

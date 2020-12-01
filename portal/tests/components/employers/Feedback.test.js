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
    wrapper = shallow(
      <Feedback
        appLogic={appLogic}
        isReportingFraud={false}
        isDenyingRequest={false}
        isEmployeeNoticeInsufficient={false}
        comment=""
        setComment={() => {}}
      />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when fraud is reported", () => {
    beforeEach(() => {
      wrapper = mount(
        <Feedback
          appLogic={appLogic}
          isReportingFraud
          isDenyingRequest
          isEmployeeNoticeInsufficient={false}
          comment=""
          setComment={() => {}}
        />
      );
    });

    it("disables the 'no' option and selects 'yes'", () => {
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    it("displays a message prompting user to leave a comment about fraud", () => {
      const message = wrapper.find(".text-error").text();

      expect(message).toEqual(
        "Please tell us why you believe this is fraudulent."
      );
    });
  });

  describe("when employee notice is within less than a month timeframe", () => {
    beforeEach(() => {
      wrapper = mount(
        <Feedback
          appLogic={appLogic}
          isReportingFraud={false}
          isDenyingRequest={false}
          isEmployeeNoticeInsufficient
          comment=""
          setComment={() => {}}
        />
      );
    });

    it("disables the 'no' option and selects 'yes'", () => {
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    it("displays a message prompting user to leave a comment", () => {
      const message = wrapper.find(".text-error").text();

      expect(message).toEqual(
        "Please tell us when your employee notified you about their leave."
      );
    });
  });

  describe("when leave request is denied", () => {
    beforeEach(() => {
      wrapper = mount(
        <Feedback
          appLogic={appLogic}
          comment=""
          isReportingFraud={false}
          isDenyingRequest
          isEmployeeNoticeInsufficient={false}
          setComment={() => {}}
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

    it("displays a message prompting user to leave a comment about denial", () => {
      const message = wrapper.find(".text-error").text();

      expect(message).toEqual(
        "Please tell us why you denied this leave request."
      );
    });

    describe("and is then approved", () => {
      beforeEach(() => {
        wrapper = mount(
          <Feedback
            appLogic={appLogic}
            comment=""
            isReportingFraud={false}
            isDenyingRequest
            isEmployeeNoticeInsufficient={false}
            setComment={() => {}}
          />
        );

        act(() => {
          wrapper.setProps({ isDenyingRequest: false });
        });
        // for useEffect to take place
        wrapper.update();
      });

      it('re-enables the "No" option', () => {
        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.disabled).toBe(false);
      });

      it('selects the "No" option if there is no comment typed', () => {
        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.checked).toBe(true);
      });

      it('keeps "Yes" selected if there is a comment typed', () => {
        wrapper = mount(
          <Feedback
            appLogic={appLogic}
            comment="some comment"
            isDenyingRequest
            setComment={() => {}}
          />
        );

        act(() => {
          wrapper.setProps({ isDenyingRequest: false });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const yesOption = choices.find((choice) => choice.label === "Yes");
        expect(yesOption.checked).toBe(true);
      });
    });
  });

  describe("when comments are not required", () => {
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
      changeRadioGroup("shouldShowCommentBox", "true");

      expect(wrapper.find("textarea").exists()).toEqual(true);
      expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });
});

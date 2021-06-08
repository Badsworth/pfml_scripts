import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import Feedback from "../../../src/components/employers/Feedback";
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
      const message = wrapper.find("Trans").text();

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
      const message = wrapper.find("Trans").text();

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
      const message = wrapper.find("Trans").text();

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
    it("shows comment box", () => {
      const { changeRadioGroup } = simulateEvents(wrapper);
      changeRadioGroup("shouldShowCommentBox", "true");

      expect(wrapper.find("textarea").exists()).toEqual(true);
      // TODO (EMPLOYER-665): Show file upload
      // expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });

  it("renders inline error message when the text exceeds the limit", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "comment",
        type: "maxLength",
        message:
          "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
      }),
    ]);
    appLogic.appErrors = appErrors;
    wrapper = mount(
      <Feedback
        appLogic={appLogic}
        comment="some comment"
        isDenyingRequest
        setComment={() => {}}
      />
    );

    expect(
      wrapper.find("ConditionalContent").find("FormLabel").find("span").text()
    ).toMatchInlineSnapshot(
      `"Please shorten your comment. We cannot accept comments that are longer than 9999 characters."`
    );
    expect(
      wrapper
        .find("ConditionalContent")
        .find("textarea[name='comment']")
        .hasClass("usa-input--error")
    ).toEqual(true);
  });
});

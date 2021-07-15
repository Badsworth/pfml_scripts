import { mount, shallow } from "enzyme";
import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import Feedback from "../../../src/components/employers/Feedback";
import React from "react";
import { act } from "react-dom/test-utils";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const getField = jest.fn();
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: { comment: "" },
        updateFields,
      });
    });
  });

  function render(renderMode = "shallow", givenProps = {}) {
    const defaultProps = {
      getField,
      getFunctionalInputProps,
      isReportingFraud: false,
      isDenyingRequest: false,
      isEmployeeNoticeInsufficient: false,
      comment: "",
      updateFields,
    };
    const props = { ...defaultProps, ...givenProps };
    if (renderMode === "mount") {
      return mount(<Feedback {...props} />);
    } else {
      return shallow(<Feedback {...props} />);
    }
  }

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  describe("when fraud is reported", () => {
    it("disables the 'no' option and selects 'yes'", () => {
      const wrapper = render("mount", {
        isReportingFraud: true,
        isDenyingRequest: true,
      });
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    it("displays a message prompting user to leave a comment about fraud", () => {
      const wrapper = render("mount", {
        isReportingFraud: true,
        isDenyingRequest: true,
      });
      const message = wrapper.find("Trans").text();

      expect(message).toEqual(
        "Please tell us why you believe this is fraudulent."
      );
    });
  });

  describe("when employee notice is within less than a month timeframe", () => {
    it("disables the 'no' option and selects 'yes'", () => {
      const wrapper = render("mount", { isEmployeeNoticeInsufficient: true });
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    it("displays a message prompting user to leave a comment", () => {
      const wrapper = render("mount", { isEmployeeNoticeInsufficient: true });
      const message = wrapper.find("Trans").text();

      expect(message).toEqual(
        "Please tell us when your employee notified you about their leave."
      );
    });
  });

  describe("when leave request is denied", () => {
    it("disables the 'No' option and selects 'Yes'", () => {
      const wrapper = render("mount", { isDenyingRequest: true });
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBe(true);
      expect(yesOption.checked).toBe(true);
    });

    it("displays a message prompting user to leave a comment about denial", () => {
      const wrapper = render("mount", { isDenyingRequest: true });
      const message = wrapper.find("Trans").text();

      expect(message).toEqual(
        "Please tell us why you denied this leave request."
      );
    });

    describe("and is then approved", () => {
      it('re-enables the "No" option', () => {
        const wrapper = render("mount", { isDenyingRequest: true });
        act(() => {
          wrapper.setProps({ isDenyingRequest: false });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.disabled).toBe(false);
      });

      it('selects the "No" option if there is no comment typed', () => {
        const wrapper = render("mount", { isDenyingRequest: true });
        act(() => {
          wrapper.setProps({ isDenyingRequest: false });
        });
        // for useEffect to take place
        wrapper.update();

        const choices = wrapper.find("InputChoiceGroup").prop("choices");
        const noOption = choices.find((choice) => choice.label === "No");
        expect(noOption.checked).toBe(true);
      });

      it('keeps "Yes" selected if there is a comment typed', () => {
        const wrapper = render("mount", {
          comment: "some comment",
          isDenyingRequest: true,
        });
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
      const wrapper = render();
      const choices = wrapper.find("InputChoiceGroup").prop("choices");
      const noOption = choices.find((choice) => choice.label === "No");
      const yesOption = choices.find((choice) => choice.label === "Yes");

      expect(noOption.disabled).toBeFalsy();
      expect(yesOption.disabled).toBeFalsy();
    });
  });

  describe("when user selects option to leave additional comments", () => {
    it("shows comment box", () => {
      const wrapper = render();
      const { changeRadioGroup } = simulateEvents(wrapper);
      changeRadioGroup("shouldShowCommentBox", "true");

      expect(wrapper.find("textarea").exists()).toEqual(true);
      // TODO (EMPLOYER-665): Show file upload
      // expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });

  it.only("renders inline error message when the text exceeds the limit", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "comment",
        type: "maxLength",
        message:
          "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
      }),
    ]);
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors,
        formState: { comment: "" },
        updateFields,
      });
    });
    const wrapper = render("mount", { getFunctionalInputProps });

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

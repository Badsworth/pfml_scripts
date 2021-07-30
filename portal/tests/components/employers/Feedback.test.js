import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import Feedback from "../../../src/components/employers/Feedback";
import React from "react";
import { testHook } from "../../test-utils";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  function render(givenProps = {}, renderMode = "shallow") {
    const defaultProps = {
      context: "",
      getFunctionalInputProps,
      shouldDisableNoOption: false,
      shouldShowCommentBox: false,
    };

    const props = { ...defaultProps, ...givenProps };
    if (renderMode === "shallow") {
      return shallow(<Feedback {...props} />);
    } else {
      return mount(<Feedback {...props} />);
    }
  }

  function setUpFunctionalInputProps(customArgs = {}) {
    const defaultArgs = {
      appErrors: new AppErrorInfoCollection(),
      formState: {},
      updateFields,
    };
    const args = { ...defaultArgs, ...customArgs };
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps(args);
    });
  }

  beforeEach(() => {
    setUpFunctionalInputProps();
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("disables the 'No' option based on 'shouldDisableNoOption' prop", () => {
    const wrapper = render({
      shouldDisableNoOption: true,
      shouldShowCommentBox: true,
    });
    const noOption = wrapper
      .find("InputChoiceGroup")
      .prop("choices")
      .find((choice) => choice.label === "No");
    expect(noOption.disabled).toBe(true);
  });

  describe("when 'shouldShowCommentBox' is true", () => {
    function renderWithCommentBoxShown(props = {}) {
      return render({ ...props, shouldShowCommentBox: true });
    }

    function getSolicitationMessage(wrapper) {
      return wrapper
        .find({ "data-test": "feedback-comment-solicitation" })
        .dive()
        .text();
    }

    it("shows the comment box", () => {
      const wrapper = renderWithCommentBoxShown();
      expect(wrapper.find('textarea[name="comment"]').exists()).toBe(true);
    });

    it("displays the correct default help message", () => {
      const wrapper = renderWithCommentBoxShown();
      const message = getSolicitationMessage(wrapper);

      expect(message).toEqual("Please tell us more.");
    });

    it("displays the correct help message for 'fraud' context ", () => {
      const wrapper = render({
        shouldShowCommentBox: true,
        context: "fraud",
      });
      const message = getSolicitationMessage(wrapper);

      expect(message).toEqual(
        "Please tell us why you believe this is fraudulent."
      );
    });

    it("displays the correct help message for 'employerDecision' context", () => {
      const wrapper = render({
        shouldShowCommentBox: true,
        context: "employerDecision",
      });
      const message = getSolicitationMessage(wrapper);

      expect(message).toEqual(
        "Please tell us why you denied this leave request."
      );
    });

    it("displays the correct help message for 'employeeNotice' context", () => {
      const wrapper = render({
        shouldShowCommentBox: true,
        context: "employeeNotice",
      });
      const message = getSolicitationMessage(wrapper);

      expect(message).toEqual(
        "Please tell us when your employee notified you about their leave."
      );
    });
  });

  it("renders inline error message when the text exceeds the limit", () => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection([
          new AppErrorInfo({
            field: "comment",
            type: "maxLength",
            message:
              "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
          }),
        ]),
        formState: {},
        updateFields,
      });
    });
    const wrapper = render(
      {
        getFunctionalInputProps,
        shouldShowCommentBox: true,
      },
      "mount"
    );

    expect(wrapper.find("FormLabel").find("span").text()).toMatchInlineSnapshot(
      `"Please shorten your comment. We cannot accept comments that are longer than 9999 characters."`
    );
    expect(
      wrapper.find("textarea[name='comment']").hasClass("usa-input--error")
    ).toEqual(true);
  });
});

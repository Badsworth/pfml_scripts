import Feedback from "../../../src/components/employers/Feedback";
import FileCardList from "../../../src/components/FileCardList";
import React from "react";
import { shallow } from "enzyme";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const appLogic = useAppLogic();
  const wrapper = shallow(<Feedback appLogic={appLogic} />);
  const { changeRadioGroup } = simulateEvents(wrapper);

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user selects option to leave additional comments", () => {
    it("shows comment box and file upload button", () => {
      changeRadioGroup("employer-review-options", "Yes");

      expect(wrapper.find("#employer-comment").exists()).toEqual(true);
      expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });

  describe("when user selects option to not leave additional comments", () => {
    it("hides comment box and file upload button", () => {
      changeRadioGroup("employer-review-options", "No");

      expect(wrapper.find("#employer-comment").exists()).toEqual(false);
      expect(wrapper.find(FileCardList).exists()).toEqual(false);
    });
  });
});

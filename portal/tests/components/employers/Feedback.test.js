import Feedback from "../../../src/components/employers/Feedback";
import FileCardList from "../../../src/components/FileCardList";
import React from "react";
import { shallow } from "enzyme";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const appLogic = useAppLogic();
  const wrapper = shallow(<Feedback appLogic={appLogic} onSubmit={() => {}} />);
  const { changeRadioGroup } = simulateEvents(wrapper);

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user selects option to leave additional comments", () => {
    it("shows comment box and file upload button", () => {
      changeRadioGroup("hasComment", "true");

      expect(wrapper.find("textarea").exists()).toEqual(true);
      expect(wrapper.find(FileCardList).exists()).toEqual(true);
    });
  });
});

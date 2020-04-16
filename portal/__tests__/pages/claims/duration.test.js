import ConnectedDuration, {
  Duration,
} from "../../../src/pages/claims/duration";
import React from "react";
import { initializeStore } from "../../../src/store";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("Duration", () => {
  it("renders connected component", () => {
    const wrapper = shallow(<ConnectedDuration store={initializeStore()} />);
    expect(wrapper).toMatchSnapshot();
  });

  it("initially renders the page without conditional fields", () => {
    const wrapper = shallow(
      <Duration
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{}}
      />
    );
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  describe("regardless of durationType value", () => {
    const wrapper = shallow(
      <Duration
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{}}
      />
    );

    it("redirects to the home page", () => {
      expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
        routes.home
      );
    });
  });

  describe("when user indicates that leave is continuous", () => {
    const wrapper = shallow(
      <Duration
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{ durationType: "continuous" }}
      />
    );

    it("doesn't render conditional fields", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });
  });

  describe("when user indicates that leave is intermittent", () => {
    const wrapper = shallow(
      <Duration
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{ durationType: "intermittent" }}
      />
    );

    it("renders conditional field", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeTruthy();
    });
  });
});

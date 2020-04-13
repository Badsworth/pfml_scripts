import ConnectedStateId, { StateId } from "../../../src/pages/claims/state-id";
import React from "react";
import initializeStore from "../../../src/store";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("StateId", () => {
  it("renders the connected component", () => {
    const wrapper = shallow(<ConnectedStateId store={initializeStore()} />);
    expect(wrapper).toMatchSnapshot();
  });

  it("initially renders the page without an id field", () => {
    const wrapper = shallow(
      <StateId
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{}}
      />
    );
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  describe("when user indicates they have a state id", () => {
    const wrapper = shallow(
      <StateId
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{ hasStateId: true }}
      />
    );

    it("renders id field", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeTruthy();
    });

    it("will redirect to home", () => {
      expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
        routes.home
      );
    });
  });

  describe("when user indicates they do NOT have a state id", () => {
    const wrapper = shallow(
      <StateId
        updateFieldFromEvent={jest.fn()}
        removeField={jest.fn()}
        formData={{ hasStateId: false }}
      />
    );

    it("will redirect to ssn page", () => {
      expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
        routes.claims.ssn
      );
    });
  });
});

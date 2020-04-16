import ConnectedSsn, { Ssn } from "../../../src/pages/claims/ssn";
import { mount, shallow } from "enzyme";
import React from "react";
import { initializeStore } from "../../../src/store";
import routes from "../../../src/routes";

describe("Ssn", () => {
  it("renders connected component", () => {
    const wrapper = shallow(
      <ConnectedSsn
        store={initializeStore({
          form: {
            ssn: "",
          },
        })}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the form", () => {
    const wrapper = shallow(
      <Ssn updateFieldFromEvent={jest.fn()} formData={{}} />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to home if unrestrictedClaimFlow is not enabled", () => {
    const wrapper = shallow(
      <Ssn updateFieldFromEvent={jest.fn()} formData={{}} />
    );

    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(routes.home);
  });

  it("redirects to leaveType if unrestrictedClaimFlow is enabled", () => {
    process.env = {
      ...process.env,
      featureFlags: {
        unrestrictedClaimFlow: true,
      },
    };

    const wrapper = shallow(
      <Ssn updateFieldFromEvent={jest.fn()} formData={{}} />
    );

    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      routes.claims.leaveType
    );
  });

  it("calls updateFieldFromEvent with user input", () => {
    const store = initializeStore();
    const wrapper = mount(<ConnectedSsn store={store} />);
    const inputData = {
      ssn: "555-55-5555",
    };

    for (const key in inputData) {
      const value = inputData[key];
      const event = { target: { name: key, value } };
      wrapper.find({ name: key, type: "text" }).simulate("change", event);
      expect(wrapper.find({ name: key, type: "text" }).prop("value")).toEqual(
        value
      );
    }
  });
});

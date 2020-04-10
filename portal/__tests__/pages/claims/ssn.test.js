import ConnectedSsn, { Ssn } from "../../../src/pages/claims/ssn";
import { mount, shallow } from "enzyme";
import React from "react";
import initializeStore from "../../../src/store";

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

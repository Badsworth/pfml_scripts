import * as nextRouter from "next/router";
import ConnectedEmployeeInfo, {
  EmployeeInfo,
} from "../../../src/pages/eligibility/employee-info";
import { mount, shallow } from "enzyme";
import React from "react";
import { initializeStore } from "../../../src/store";

describe("EmployeeInfo", () => {
  it("render connected component", () => {
    const wrapper = shallow(
      <ConnectedEmployeeInfo
        store={initializeStore({
          form: {
            firstName: "",
            middleName: "",
            lastName: "",
            ssnOrItin: "",
          },
        })}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the form", () => {
    const wrapper = shallow(
      <EmployeeInfo updateFieldFromEvent={jest.fn()} formData={{}} />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("calls updateFieldFromEvent with user input", () => {
    const store = initializeStore();
    const wrapper = mount(<ConnectedEmployeeInfo store={store} />);
    const inputData = {
      firstName: "James",
      middleName: "AA",
      lastName: "Joyce",
      ssnOrItin: "222222222",
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

  it("redirects to wages after submit", () => {
    const useRouter = jest.spyOn(nextRouter, "useRouter");
    const push = jest.fn();
    useRouter.mockImplementation(() => ({ push }));

    // recreate component using mocked router
    const wrapper = shallow(
      <EmployeeInfo updateFieldFromEvent={jest.fn()} formData={{}} />
    );

    const event = { preventDefault: jest.fn() };
    wrapper.find("form").simulate("submit", event);

    expect(push).toHaveBeenCalledWith(
      expect.stringMatching(/eligibility\/result.*/)
    );
  });
});

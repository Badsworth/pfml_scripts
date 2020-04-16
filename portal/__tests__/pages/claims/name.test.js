import ConnectedNamePage, { Name } from "../../../src/pages/claims/name";
import React from "react";
import { initializeStore } from "../../../src/store";
import { shallow } from "enzyme";

describe("Name", () => {
  it("renders the connected component", () => {
    const wrapper = shallow(
      <ConnectedNamePage
        store={initializeStore({
          form: {
            firstName: "Aquib",
            middleName: "cricketer",
            lastName: "Khan",
          },
        })}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page", () => {
    const wrapper = shallow(
      <Name updateFieldFromEvent={jest.fn()} formData={{}} />
    );
    expect(wrapper).toMatchSnapshot();
  });
});

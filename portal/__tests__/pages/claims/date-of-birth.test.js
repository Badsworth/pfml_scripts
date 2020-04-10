import ConnectedDateOfBirthPage, {
  DateOfBirth,
} from "../../../src/pages/claims/date-of-birth";
import React from "react";
import initializeStore from "../../../src/store";
import { shallow } from "enzyme";

describe("DateOfBirth", () => {
  it("renders the connected component", () => {
    const wrapper = shallow(
      <ConnectedDateOfBirthPage
        store={initializeStore({
          form: {
            dateOfBirth: "02-12-1809",
          },
        })}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page", () => {
    const wrapper = shallow(
      <DateOfBirth updateFieldFromEvent={jest.fn()} formData={{}} />
    );
    expect(wrapper).toMatchSnapshot();
  });
});

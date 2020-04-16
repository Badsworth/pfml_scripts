import ConnectedLeaveType, {
  LeaveType,
} from "../../../src/pages/claims/leave-type";
import React from "react";
import initializeStore from "../../../src/store";
import { shallow } from "enzyme";

describe("LeaveType", () => {
  it("renders the connected component", () => {
    const wrapper = shallow(<ConnectedLeaveType store={initializeStore({})} />);
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page", () => {
    const wrapper = shallow(
      <LeaveType
        updateFieldFromEvent={jest.fn()}
        formData={{
          leaveType: "parentalLeave",
        }}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });
});

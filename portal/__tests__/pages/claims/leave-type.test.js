import { mount, shallow } from "enzyme";
import Claim from "../../../src/models/Claim";
import { LeaveType } from "../../../src/pages/claims/leave-type";
import React from "react";
import claimsApi from "../../../src/api/claimsApi";
claimsApi.updateClaim = jest.fn().mockReturnValue({ success: true });

const render = (props = {}, mountComponent) => {
  const claim_id = "12345";
  const claim = new Claim({ claim_id });

  const renderFn = mountComponent ? mount : shallow;

  return {
    props: {
      claim,
      ...props,
    },
    wrapper: renderFn(<LeaveType claim={claim} {...props} />),
  };
};

describe("LeaveType", () => {
  it("renders the page", () => {
    const { wrapper } = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("updates claim in API when user submits", () => {
    const { wrapper } = render({}, true);
    const event = { preventDefault: jest.fn() };
    wrapper.find("form").simulate("submit", event);

    expect(claimsApi.updateClaim).toHaveBeenCalled();
  });

  it("updates portal claim state", async () => {
    const { props, wrapper } = render({ updateClaim: jest.fn() }, true);
    const event = { preventDefault: jest.fn() };
    await wrapper.find("form").simulate("submit", event);
    expect(props.updateClaim).toHaveBeenCalled();
  });
});

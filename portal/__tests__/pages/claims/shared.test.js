/**
 * @file test behavior and features common to all claims pages
 */

import Claim from "../../../src/models/Claim";
import ClaimsApi from "../../../src/api/ClaimsApi";
import { Duration } from "../../../src/pages/claims/duration";
import { LeaveDates } from "../../../src/pages/claims/leave-dates";
import { LeaveType } from "../../../src/pages/claims/leave-type";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import React from "react";
import User from "../../../src/models/User";
import { mount } from "enzyme";

const testPages = [LeaveType, LeaveDates, Duration, NotifiedEmployer];

const render = (Component, _props = {}) => {
  const application_id = "12345";
  const claim = new Claim({ application_id });
  const user = new User({ user_id: "mock-user-id" });
  const claimsApi = new ClaimsApi({ user });
  jest.spyOn(claimsApi, "updateClaim");
  claimsApi.updateClaim.mockReturnValue({ success: true });

  const props = {
    claim,
    claimsApi,
    ..._props,
  };

  return {
    props,
    wrapper: mount(<Component claim={claim} {...props} />),
  };
};

describe("Shared claims page behavior", () => {
  for (const Page of testPages) {
    describe(Page.name, () => {
      it("updates claim in API when user submits", () => {
        const { wrapper, props } = render(Page);
        const event = { preventDefault: jest.fn() };
        wrapper.find("form").simulate("submit", event);

        expect(props.claimsApi.updateClaim).toHaveBeenCalledTimes(1);
      });

      it("updates portal claim state", async () => {
        const { props, wrapper } = render(Page, { updateClaim: jest.fn() });
        const event = { preventDefault: jest.fn() };

        await wrapper.find("form").simulate("submit", event);
        expect(props.updateClaim).toHaveBeenCalledTimes(1);
      });
    });
  }
});

/**
 * @file test behavior and features common to all claims pages
 */

import Claim from "../../../src/models/Claim";
import { Duration } from "../../../src/pages/claims/duration";
import { LeaveDates } from "../../../src/pages/claims/leave-dates";
import { LeaveType } from "../../../src/pages/claims/leave-type";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import React from "react";
import claimsApi from "../../../src/api/claimsApi";
import { mount } from "enzyme";

const testPages = [LeaveType, LeaveDates, Duration, NotifiedEmployer];

const render = (Component, props = {}) => {
  const claim_id = "12345";
  const claim = new Claim({ claim_id });

  return {
    props: {
      claim,
      ...props,
    },
    wrapper: mount(<Component claim={claim} {...props} />),
  };
};

describe("Shared claims page behavior", () => {
  claimsApi.updateClaim = jest.fn().mockReturnValue({ success: true });

  for (const Page of testPages) {
    describe(Page.name, () => {
      it("updates claim in API when user submits", () => {
        const { wrapper } = render(Page);
        const event = { preventDefault: jest.fn() };
        wrapper.find("form").simulate("submit", event);

        expect(claimsApi.updateClaim).toHaveBeenCalled();
      });

      it("updates portal claim state", async () => {
        const { props, wrapper } = render(Page, { updateClaim: jest.fn() });
        const event = { preventDefault: jest.fn() };

        await wrapper.find("form").simulate("submit", event);
        expect(props.updateClaim).toHaveBeenCalled();
      });
    });
  }
});

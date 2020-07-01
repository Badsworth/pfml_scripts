/**
 * @file test behavior and features common to all claims pages
 */
import Claim from "../../../src/models/Claim";
import { Duration } from "../../../src/pages/claims/duration";
import { LeaveDates } from "../../../src/pages/claims/leave-dates";
import { LeaveReasonPage } from "../../../src/pages/claims/leave-reason";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import React from "react";
import { mount } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

const testPages = [LeaveReasonPage, LeaveDates, Duration, NotifiedEmployer];

const render = (Component, _props = {}) => {
  const application_id = "12345";
  const claim = new Claim({ application_id });
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const appLogic = useAppLogic();

  const props = {
    claim,
    appLogic,
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

        expect(props.appLogic.updateClaim).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(Object)
        );
      });
    });
  }
});

import { simulateEvents, testHook } from "../../../test-utils";
import React from "react";
import Verification from "../../../../src/pages/employers/claims/verification";
import { shallow } from "enzyme";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Verification", () => {
  const query = { absence_id: "mock-absence-id" };
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(
      <Verification appLogic={appLogic} query={query} />
    ).dive();
  });

  it("renders verification page", () => {
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("calls goToNextPage when user clicks submit button", () => {
    const { submitForm } = simulateEvents(wrapper);

    submitForm();

    expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
      {},
      { absence_id: "mock-absence-id" }
    );
  });
});

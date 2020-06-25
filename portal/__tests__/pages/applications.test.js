import Applications from "../../src/pages/applications";
import Claim from "../../src/models/Claim";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Applications", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    appLogic.claims = appLogic.claims.addItem(
      new Claim({ application_id: "mock_claim_id" })
    );

    wrapper = shallow(<Applications appLogic={appLogic} />);
  });

  it("renders page title", () => {
    // Not taking a snapshot of the entire page in order to avoid
    // the snapshot changing every time the Claim model changes
    expect(wrapper.find("Title")).toMatchInlineSnapshot(`
      <Title
        marginBottom="4"
      >
        In-progress applications
      </Title>
    `);
  });

  it("renders list of Applications", () => {
    expect(wrapper.find("ApplicationCard")).toHaveLength(1);
  });
});

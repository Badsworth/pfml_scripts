import Index from "../../../src/pages/employers/index";
import React from "react";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { mount } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("redirects to Claim Review page", () => {
    act(() => {
      mount(<Index appLogic={appLogic} />);
    });

    expect(mockRouter.push).toHaveBeenCalledWith("/employers/claims/review");
  });
});

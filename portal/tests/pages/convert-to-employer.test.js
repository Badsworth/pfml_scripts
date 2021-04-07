import User, { RoleDescription } from "../../src/models/User";
import {
  renderWithAppLogic,
  simulateEvents,
  testHook
} from "../test-utils";
import ConvertToEmployer from "../../src/pages/convert-to-employer";
import React from "react";
import { shallow } from "enzyme";
import tracker from "../../src/services/tracker";
import useAppLogic from "../../src/hooks/useAppLogic";

import ClaimCollection from "../../src/models/ClaimCollection";
import GetReady from "../../src/pages/applications/get-ready";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import routes from "../../src/routes";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");
jest.mock("../../src/hooks/useAppLogic");

describe("ConvertToEmployer", () => {
  function render(customProps = {}, options = { claims: [] }) {
    let appLogic, claims, user

    testHook(() => {
      appLogic = useAppLogic();
      claims = new ClaimCollection(options.claims);
      user = new User({ consented_to_data_sharing: true });
    });
    
    const { wrapper } = renderWithAppLogic(ConvertToEmployer, {
      diveLevels: 0,
      render: "mount",
      props: { appLogic, claims, user, ...customProps },
    });

    return {appLogic, claims, user, wrapper}
  }

  it("renders form", () => { 
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });
  it("submits an FEIN", async () => {
    const fein = "123456789"
    const {appLogic, wrapper} = render();
    const { changeField, submitForm } = simulateEvents(wrapper);
    changeField("employer_fein", fein);
    await submitForm();
    expect(appLogic.claims.update).toHaveBeenCalledWith(
      expect.any(String),
      {
        "role": { 
          "role_description": RoleDescription.employer 
        },
        "user_leave_administrator": {
            "employer_fein": fein
        }
      } 
      );
  })
})

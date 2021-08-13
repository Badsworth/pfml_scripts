import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "../../src/components/ApplicationCardV2";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCardV2", () => {
  let props;
  const render = (claim, additionalProps = {}) => {
    props = Object.assign(
      {
        appLogic: {
          appErrors: new AppErrorInfoCollection([]),
          documents: {
            download: jest.fn(),
          },
        },
        documents: [],
      },
      additionalProps
    );

    return shallow(<ApplicationCardV2 claim={claim} number={2} {...props} />);
  };

  describe("when the claim status is Completed", () => {
    it("matches existing snapshot", () => {
      const wrapper = render(new MockBenefitsApplicationBuilder().create());
      expect(wrapper).toMatchSnapshot();
    });
  });
});

import { makeFile, testHook } from "../../test-utils";
import React from "react";
import UploadOtherId from "../../../src/pages/claims/upload-other-id";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

const claim_id = "12345";

describe("UploadOtherId", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic({ user: {} });
    });
    ({ wrapper } = render());
  });

  const render = (props = {}) => {
    const allProps = {
      query: { claim_id },
      appLogic,
      ...props,
    };

    return {
      props: allProps,
      wrapper: shallow(<UploadOtherId {...allProps} />),
    };
  };

  it("initially renders the page without any filecards", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user uploads files", () => {
    it("renders filecards for the files", () => {
      const files = [makeFile(), makeFile(), makeFile()];
      const event = {
        target: {
          files,
        },
      };
      ({ wrapper } = render());
      const input = wrapper.find("FileCardList").dive().find("input");
      input.simulate("change", event);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the form is successfully submitted", () => {
    it.todo("uploads the files to the API");
  });
});

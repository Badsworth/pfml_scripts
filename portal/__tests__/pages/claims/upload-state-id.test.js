import React from "react";
import UploadStateId from "../../../src/pages/claims/upload-state-id";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

const claim_id = "12345";

const makeFile = (attrs = {}) => {
  const { name, type } = Object.assign(
    {
      name: "file.pdf",
      type: "application/pdf",
    },
    attrs
  );

  return new File([], name, { type });
};

const render = (props = {}) => {
  const allProps = {
    query: { claim_id },
    ...props,
  };
  return {
    props: allProps,
    wrapper: shallow(<UploadStateId {...allProps} />),
  };
};

describe("UploadStateId", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = render());
  });

  it("initially renders the page without any filecards", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("will redirect to ssn page", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.ssn}?claim_id=${claim_id}`
    );
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

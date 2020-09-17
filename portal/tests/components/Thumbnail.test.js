/* eslint-disable import/first */
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  // Mock useEffect so that we can manipulate it below
  useEffect: jest.fn(),
}));

import React, { useEffect } from "react";
import Thumbnail from "../../src/components/Thumbnail";
import { shallow } from "enzyme";

describe("Thumbnail", () => {
  const file = new File(["foo"], "foo.png", { type: "image/png" });

  beforeAll(() => {
    // URL.createObjectURL() hasn't been implemented in the jest DOM yet but will be
    // eventually. When it is (and this error triggers) we should remove this mock.
    // Read more: https://github.com/jsdom/jsdom/issues/1721
    if (URL.createObjectURL) {
      throw new Error(
        "jest DOM has added URL.createObjectURL() -- we can remove this hack now"
      );
    }
    URL.createObjectURL = () => "image.png";
    URL.revokeObjectURL = jest.fn();
  });

  describe("when initially loading the preview", () => {
    it("renders nothing", () => {
      const wrapper = shallow(<Thumbnail file={file} />);

      expect(wrapper.isEmptyRender()).toBe(true);
    });
  });

  describe("when selected file is a PDF", () => {
    it("renders placeholder thumbnail", () => {
      useEffect.mockImplementationOnce((didUpdate) => didUpdate());
      const pdfFile = new File(["foo"], "bar.pdf", { type: "application/pdf" });

      const wrapper = shallow(<Thumbnail file={pdfFile} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when selected file is an image", () => {
    it("renders the img using a created URL", () => {
      useEffect.mockImplementationOnce((f) => f());
      const createUrlSpy = jest.spyOn(URL, "createObjectURL");

      const wrapper = shallow(<Thumbnail file={file} />);

      expect(createUrlSpy).toHaveBeenCalledTimes(1);
      expect(wrapper.prop("style")).toMatchInlineSnapshot(`
        Object {
          "backgroundImage": "url(image.png)",
        }
      `);
    });

    it("cleans up the created URL", () => {
      useEffect.mockImplementationOnce((f) => {
        const unmount = f();
        unmount();
      });
      const revokeUrlSpy = jest.spyOn(URL, "revokeObjectURL");

      shallow(<Thumbnail file={file} />);

      expect(revokeUrlSpy).toHaveBeenCalledTimes(1);
    });
  });
});

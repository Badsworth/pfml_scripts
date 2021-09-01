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
      expect(wrapper.find("img")).toMatchInlineSnapshot(`
        <img
          alt=""
          src="image.png"
        />
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

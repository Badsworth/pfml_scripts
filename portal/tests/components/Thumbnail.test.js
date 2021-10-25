/* eslint-disable import/first */
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  // Mock useEffect so that we can manipulate it below
  useEffect: jest.fn(),
}));

import React, { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import Thumbnail from "../../src/components/Thumbnail";

describe("Thumbnail", () => {
  const file = new File(["foo"], "foo.png", { type: "image/png" });

  describe("when initially loading the preview", () => {
    it("renders nothing", () => {
      const { container } = render(<Thumbnail file={file} />);

      expect(container).toBeEmptyDOMElement();
    });
  });

  describe("when selected file is a PDF", () => {
    it("renders placeholder thumbnail", () => {
      useEffect.mockImplementationOnce((didUpdate) => didUpdate());
      const pdfFile = new File(["foo"], "bar.pdf", { type: "application/pdf" });

      const { container } = render(<Thumbnail file={pdfFile} />);

      expect(container.firstChild).toMatchSnapshot();
    });
  });

  describe("when selected file is an image", () => {
    it("renders the img using a created URL", () => {
      useEffect.mockImplementationOnce((f) => f());
      const createUrlSpy = jest.spyOn(URL, "createObjectURL");

      render(<Thumbnail file={file} />);
      expect(createUrlSpy).toHaveBeenCalledTimes(1);
      expect(screen.getByRole("img")).toMatchInlineSnapshot(`
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

      render(<Thumbnail file={file} />);

      expect(revokeUrlSpy).toHaveBeenCalledTimes(1);
    });
  });
});

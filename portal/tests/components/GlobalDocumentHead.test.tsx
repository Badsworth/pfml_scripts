import { cleanup, render } from "@testing-library/react";
import GlobalDocumentHead from "../../src/components/GlobalDocumentHead";
import React from "react";

describe("GlobalDocumentHead", () => {
  it("renders head tags", () => {
    const { container } = render(<GlobalDocumentHead />);

    expect(container.children).toMatchSnapshot();
  });

  it("blocks search engines in lower environments", () => {
    const metaSelector = 'meta[content="noindex"]';
    render(<GlobalDocumentHead />);

    expect(document.querySelector(metaSelector)).toBeInTheDocument();

    cleanup();
    process.env.BUILD_ENV = "prod";
    render(<GlobalDocumentHead />);

    expect(document.querySelector(metaSelector)).not.toBeInTheDocument();
  });
});

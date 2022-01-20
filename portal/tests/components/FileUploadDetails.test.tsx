import FileUploadDetails from "../../src/components/FileUploadDetails";
import React from "react";
import { render } from "@testing-library/react";

describe("FileUploadDetails", () => {
  it("renders the details with text", () => {
    const { container } = render(<FileUploadDetails />);
    expect(container.firstChild).toMatchSnapshot();
  });
});

import { render, screen } from "@testing-library/react";
import Document from "../../src/models/Document";
import FileCard from "../../src/components/FileCard";
import React from "react";
import userEvent from "@testing-library/user-event";

const onRemove = jest.fn();
const renderFile = (customProps) => {
  const file = new File(["foo"], "foo.png", { type: "image/png" });

  const defaultProps = {
    heading: "Document 1",
    file,
    onRemoveClick: onRemove,
    ...customProps,
  };
  return render(<FileCard {...defaultProps} />);
};

describe("FileCard", () => {
  it("renders a file", () => {
    const { container } = renderFile();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls onRemove handler when remove button is clicked", () => {
    renderFile();
    expect(onRemove).not.toHaveBeenCalled();
    userEvent.click(screen.getByRole("button", { name: "Remove file" }));
    expect(onRemove).toHaveBeenCalled();
  });

  it("renders an error message when indicated", () => {
    renderFile({ errorMsg: "Hallo I am an error" });
    expect(screen.getByText(/Hallo I am an error/)).toBeInTheDocument();
  });

  it("with a document, no button is rendered", () => {
    renderFile({ document: new Document({ created_at: "2021-11-11" }) });
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("with a document, displays the date uploaded", () => {
    renderFile({ document: new Document({ created_at: "2021-11-11" }) });
    expect(screen.getByText("Date of upload: 11/11/2021")).toBeInTheDocument();
  });
});

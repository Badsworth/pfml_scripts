import { render, screen, within } from "@testing-library/react";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import { DocumentType } from "../../src/models/Document";
import { DocumentsUploadError } from "../../src/errors";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import TempFile from "../../src/models/TempFile";
import { act } from "react-dom/test-utils";
import { makeFile } from "../test-utils";
import userEvent from "@testing-library/user-event";

const makeFileObjectHelper = (attrs = {}) => {
  const fileAttrs = attrs.id ? { id: attrs.id } : {};
  fileAttrs.file = makeFile(attrs);
  return new TempFile(fileAttrs);
};

const onChange = jest.fn();
const onRemoveTempFile = jest.fn();

const renderComponent = (customProps) => {
  const defaultProps = {
    documents: [],
    tempFiles: new ApiResourceCollection("id"),
    onChange,
    fileErrors: [],
    onRemoveTempFile,
    fileHeadingPrefix: "Document",
    addFirstFileButtonText: "Choose a document",
    addAnotherFileButtonText: "Choose another document",
    disableRemove: false,
    ...customProps,
  };
  return render(<FileCardList {...defaultProps} />);
};

describe("FileCardList", () => {
  it("renders an empty list when no documents available", () => {
    renderComponent();
    const [documentFileCards, fileCards] = screen.getAllByRole("list");
    expect(documentFileCards).toBeEmptyDOMElement();
    expect(fileCards).toBeEmptyDOMElement();
  });

  it("when temp files is empty, renders first file button text", () => {
    renderComponent({ addFirstFileButtonText: "Custom chooser" });
    expect(screen.getByText(/Custom chooser/)).toBeInTheDocument();
  });

  it("with previously selected files, renders them and user can remove", () => {
    renderComponent({
      tempFiles: new ApiResourceCollection("id", [
        makeFileObjectHelper({ name: "TempFile1.pdf" }),
      ]),
    });
    const [documentFileCards, fileCards] = screen.getAllByRole("list");
    expect(documentFileCards).toBeEmptyDOMElement();
    expect(within(fileCards).getByText(/Document 1/)).toBeInTheDocument();
    expect(within(fileCards).getByText(/TempFile1.pdf/)).toBeInTheDocument();
    expect(
      within(fileCards).getByRole("button", { name: "Remove file" })
    ).toBeInTheDocument();

    expect(onRemoveTempFile).not.toHaveBeenCalled();
    userEvent.click(screen.getByRole("button", { name: "Remove file" }));
    expect(onRemoveTempFile).toHaveBeenCalled();
  });

  it("calls onChange with a single file when user makes that selection", async () => {
    const newFile = new File([""], "filename.txt", { type: "text/plain" });
    renderComponent({
      tempFiles: new ApiResourceCollection("id", [makeFileObjectHelper()]),
    });
    const input = screen.getByText("Choose another document");
    await act(async () => {
      await userEvent.upload(input, [newFile]);
    });
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({ name: "filename.txt" }),
    ]);
  });

  it("disables remove button on file card children when indicated", () => {
    renderComponent({
      tempFiles: new ApiResourceCollection("id", [makeFileObjectHelper()]),
      disableRemove: true,
    });
    expect(screen.getByRole("button", { name: "Remove file" })).toBeDisabled();
  });

  it("calls onChange with multiple files when user makes that selection", async () => {
    const newFile = new File([""], "filename.txt", { type: "text/plain" });
    const newFile2 = new File([""], "filename2.txt", { type: "text/plain" });
    renderComponent({
      tempFiles: new ApiResourceCollection("id", [makeFileObjectHelper()]),
    });
    const input = screen.getByText("Choose another document");
    await act(async () => {
      await userEvent.upload(input, [newFile, newFile2]);
    });
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({ name: "filename.txt" }),
      expect.objectContaining({ name: "filename2.txt" }),
    ]);

    // This tests a bug that occurs in the browser but not in unit tests. In a browser if
    // event.target.value is reset (eg to "") in the onChange handler for a file input (eg
    // <input type="file">) component then event.target.files gets reset to an empty array.
    // This test ensures that event.target.value isn't reset until after we've retrieved
    // event.target.files.
    const newFile3 = new File([""], "filename3.txt", { type: "text/plain" });

    await act(async () => {
      await userEvent.upload(screen.getByText("Choose another document"), [
        newFile3,
      ]);
    });
    expect(onChange).toHaveBeenLastCalledWith([
      expect.objectContaining({ name: "filename3.txt" }),
    ]);
  });

  it("renders file cards for documents", () => {
    const newDoc1 = {
      document_type: DocumentType.certification.medicalCertification,
      application_id: "mock_application_id",
      fineos_document_id: "testId1",
      created_at: "2020-11-26",
    };
    const newDoc2 = {
      document_type: DocumentType.certification.medicalCertification,
      application_id: "mock_application_id",
      fineos_document_id: "testId2",
      created_at: "2020-11-26",
    };
    renderComponent({
      documents: [newDoc1, newDoc2],
      tempFiles: new ApiResourceCollection("id", [makeFileObjectHelper()]),
    });
    expect(screen.getByText(/Document 1/)).toBeInTheDocument();
    expect(screen.getByText(/Document 2/)).toBeInTheDocument();
    expect(screen.getByText(/Document 3/)).toBeInTheDocument();
  });

  it("passes through errors", () => {
    renderComponent({
      fileErrors: [new DocumentsUploadError("mock_application_id", "123")],
      tempFiles: new ApiResourceCollection("id", [
        makeFileObjectHelper({ id: "123" }),
        makeFileObjectHelper({ id: "333" }),
      ]),
    });
    expect(
      screen.getByText(/encountered an error when uploading your file/)
    ).toBeInTheDocument();
  });
});

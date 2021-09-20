import Document, { DocumentType } from "../../src/models/Document";
import { fireEvent, render, screen, within } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import TempFile from "../../src/models/TempFile";
import TempFileCollection from "../../src/models/TempFileCollection";
import { act } from "react-dom/test-utils";
import { makeFile } from "../test-utils";
import userEvent from "@testing-library/user-event";

const makeFileObjectHelper = (attrs = {}) => {
  const file = new TempFile({ id: attrs.id });
  const name = attrs.name || `${file.id}.pdf`;
  const type = attrs.type || "application/pdf";

  file.file = makeFile({ name, type });

  return file;
};

const onChange = jest.fn();
const onRemoveTempFile = jest.fn();

const renderComponent = (customProps) => {
  const defaultProps = {
    tempFiles: new TempFileCollection(),
    onChange,
    fileErrors: [],
    onRemoveTempFile,
    fileHeadingPrefix: "Document",
    addFirstFileButtonText: "Choose a document",
    addAnotherFileButtonText: "Choose another document",
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
      tempFiles: new TempFileCollection([makeFileObjectHelper()]),
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
      tempFiles: new TempFileCollection([makeFileObjectHelper()]),
    });
    const input = screen.getByText("Choose another document");
    await act(async () => {
      await userEvent.upload(input, [newFile]);
    });
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({ name: "filename.txt" }),
    ]);
  });

  it("calls onChange with multiple files when user makes that selection", async () => {
    const newFile = new File([""], "filename.txt", { type: "text/plain" });
    const newFile2 = new File([""], "filename2.txt", { type: "text/plain" });
    renderComponent({
      tempFiles: new TempFileCollection([makeFileObjectHelper()]),
    });
    const input = screen.getByText("Choose another document");
    await act(async () => {
      await userEvent.upload(input, [newFile, newFile2]);
    });
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({ name: "filename.txt" }),
      expect.objectContaining({ name: "filename2.txt" }),
    ]);
  });

  it("retrieves the selected files before resetting the input's value", async () => {
    // This tests a bug that occurs in the browser but not in unit tests. In a browser if
    // event.target.value is reset (eg to "") in the onChange handler for a file input (eg
    // <input type="file">) component then event.target.files gets reset to an empty array.
    // This test ensures that event.target.value isn't reset until after we've retrieved
    // event.target.files.

    renderComponent();
    const input = screen.getByText("Choose a document");

    // setup to simulate the user selecting a single file
    const newFile = new File([""], "filename.txt", { type: "text/plain" });

    // Construct an event object which will allow us to test the order in which
    // event.target.files and event.target.value are accessed in the onChange handler.
    // We do this by defining explicit setters/getters for event.target.files and
    // event.target.value which we can spy on
    const getFilesSpy = jest.fn();
    const setValueSpy = jest.fn();
    const event = {
      target: {
        set files(files) {
          this._files = files;
        },
        get files() {
          getFilesSpy();
          // event.target.value should not have been set when this is retrieved
          expect(setValueSpy).not.toHaveBeenCalled();
          return this._files;
        },
        set value(value) {
          setValueSpy();
          // event.target.files should have already been retrieved when this is set
          this._value = value;
          expect(getFilesSpy).toHaveBeenCalled();
        },
        get value() {
          return this._value;
        },
      },
    };

    // We have to set the event's files now
    event.target.files = [newFile];

    // simulate the user selecting a single file
    await act(async () => {
      await fireEvent.change(input, event);
    });

    // Make sure all of the assertions are executed
    expect.assertions(2);
  });

  it("renders file cards for documents", () => {
    const newDoc1 = new Document({
      document_type: DocumentType.certification.medicalCertification,
      application_id: "mock_application_id",
      fineos_document_id: "testId1",
      created_at: "2020-11-26",
    });
    const newDoc2 = new Document({
      document_type: DocumentType.certification.medicalCertification,
      application_id: "mock_application_id",
      fineos_document_id: "testId2",
      created_at: "2020-11-26",
    });
    renderComponent({
      documents: [newDoc1, newDoc2],
      tempFiles: new TempFileCollection([makeFileObjectHelper()]),
    });
    expect(screen.getByText(/Document 1/)).toBeInTheDocument();
    expect(screen.getByText(/Document 2/)).toBeInTheDocument();
    expect(screen.getByText(/Document 3/)).toBeInTheDocument();
  });

  it("passes through error messages as indicated", () => {
    renderComponent({
      fileErrors: [
        new AppErrorInfo(
          { message: "Mock error message #1", meta: { file_id: "123" } },
          { message: "Mock error message #2", meta: { file_id: "222" } }
        ),
      ],
      tempFiles: new TempFileCollection([
        makeFileObjectHelper({ id: "123" }),
        makeFileObjectHelper({ id: "333" }),
      ]),
    });
    expect(screen.getByText("Mock error message #1")).toBeInTheDocument();
    expect(screen.queryByText("Mock error message #2")).not.toBeInTheDocument();
  });
});

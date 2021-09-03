import Document, { DocumentType } from "../../src/models/Document";
import { makeFile, testHook } from "../test-utils";
import FileCard from "../../src/components/FileCard";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import TempFile from "../../src/models/TempFile";
import TempFileCollection from "../../src/models/TempFileCollection";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFilesLogic from "../../src/hooks/useFilesLogic";

const makeFileObject = (attrs = {}) => {
  const file = new TempFile({ id: attrs.id });
  const name = attrs.name || `${file.id}.pdf`;
  const type = attrs.type || "application/pdf";

  file.file = makeFile({ name, type });

  return file;
};

describe("FileCardList", () => {
  function render(customProps = {}) {
    const props = Object.assign(
      {
        tempFiles: new TempFileCollection(),
        fileErrors: [],
        onChange: jest.fn(),
        onRemoveTempFile: jest.fn(),
        fileHeadingPrefix: "Document",
        addFirstFileButtonText: "Choose a document",
        addAnotherFileButtonText: "Choose another document",
      },
      customProps
    );

    const fileCardList = <FileCardList {...props} />;

    return shallow(fileCardList);
  }

  describe("with no files selected", () => {
    it("renders an empty list", () => {
      const wrapper = render();

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the first file button text", () => {
      const addFirstFileButtonText = "Choose your first file!";
      const wrapper = render({ addFirstFileButtonText });

      expect(wrapper.find("label").text()).toBe(addFirstFileButtonText);
    });
  });

  describe("with previously-selected files", () => {
    const tempFiles = new TempFileCollection([makeFileObject()]);

    it("renders a list of the files", () => {
      const wrapper = render({ tempFiles });

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the 'Add another file' button text", () => {
      const addAnotherFileButtonText = "Choose more files!";
      const wrapper = render({ tempFiles, addAnotherFileButtonText });

      expect(wrapper.find("label").text()).toBe(addAnotherFileButtonText);
    });
  });

  it("calls onRemoveTempFile when user clicks remove file", async () => {
    const newFile = makeFile({ name: "file-1.png" });
    let files, processFiles, removeFile;
    testHook(() => {
      ({ files, processFiles, removeFile } = useFilesLogic({
        clearErrors: jest.fn(),
        catchError: jest.fn(),
      }));
    });
    const processFilesMock = jest
      .fn()
      .mockImplementation((tempfiles) => processFiles(tempfiles));
    const removeTempFileMock = jest
      .fn()
      .mockImplementation((id) => removeFile(id));

    // add a new file into files
    await act(async () => {
      await processFilesMock([newFile]);
    });

    const wrapper = render({
      tempFiles: files,
      onChange: processFilesMock,
      onRemoveTempFile: removeTempFileMock,
    });

    const removedFileId = files.items[0].id;
    act(() => {
      wrapper.find("FileCard").simulate("removeClick");
    });

    expect(removeTempFileMock).toHaveBeenCalledWith(removedFileId);
    expect(files.items).toEqual([]);
  });

  describe("when the user selects file(s)", () => {
    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("calls onChange with a single file when the user selects a single file", async () => {
      const newFile = makeFile({ name: "file-1.png" });

      let files, processFiles;
      testHook(() => {
        ({ files, processFiles } = useFilesLogic({
          clearErrors: jest.fn(),
          catchError: jest.fn(),
        }));
      });

      const processFilesMock = jest
        .fn()
        .mockImplementation((tempfiles) => processFiles(tempfiles));

      await act(async () => {
        const wrapper = render({
          tempFiles: files,
          onChange: processFilesMock,
        });
        // simulate the user selecting a single file
        const input = wrapper.find("input");
        await input.simulate("change", {
          target: {
            files: [newFile],
          },
        });
      });

      expect(processFilesMock).toHaveBeenCalledWith([
        expect.objectContaining({ name: "file-1.png" }),
      ]);

      expect(files.items.map((file) => file.file.name)).toEqual(["file-1.png"]);
    });

    it("calls onChange with multiple files when the user selects multiple files", async () => {
      const newFiles = [
        makeFile({ name: "file-1.png" }),
        makeFile({ name: "file-2.png" }),
      ];

      let files, processFiles;
      testHook(() => {
        ({ files, processFiles } = useFilesLogic({
          clearErrors: jest.fn(),
          catchError: jest.fn(),
        }));
      });

      const processFilesMock = jest
        .fn()
        .mockImplementation((tempfiles) => processFiles(tempfiles));

      await act(async () => {
        const wrapper = render({
          tempFiles: files,
          onChange: processFilesMock,
        });
        // simulate the user selecting multiple files
        const input = wrapper.find("input");
        await input.simulate("change", {
          target: {
            files: newFiles,
          },
        });
      });

      expect(processFilesMock).toHaveBeenCalledWith([
        expect.objectContaining({ name: "file-1.png" }),
        expect.objectContaining({ name: "file-2.png" }),
      ]);

      expect(files.items.map((file) => file.file.name)).toEqual([
        "file-1.png",
        "file-2.png",
      ]);
    });

    it("retrieves the selected files before resetting the input's value", () => {
      // This tests a bug that occurs in the browser but not in unit tests. In a browser if
      // event.target.value is reset (eg to "") in the onChange handler for a file input (eg
      // <input type="file">) component then event.target.files gets reset to an empty array.
      // This test ensures that event.target.value isn't reset until after we've retrieved
      // event.target.files.

      const wrapper = render();
      const input = wrapper.find("input");

      // setup to simulate the user selecting a single file
      const newFile = makeFile();

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
      input.simulate("change", event);

      expect(setValueSpy).toHaveBeenCalled();
      // Make sure all of the assertions are executed
      expect.assertions(3);
    });
  });

  describe("with documents in props", () => {
    const mock_application_id = "mock_application_id";
    let newDoc1, newDoc2;
    beforeEach(() => {
      newDoc1 = new Document({
        document_type: DocumentType.certification.medicalCertification,
        application_id: mock_application_id,
        fineos_document_id: "testId1",
        created_at: "2020-11-26",
      });
      newDoc2 = new Document({
        document_type: DocumentType.certification.medicalCertification,
        application_id: mock_application_id,
        fineos_document_id: "testId2",
        created_at: "2020-11-26",
      });
    });

    it("renders a FileCard for each document", () => {
      const wrapper = render({ documents: [newDoc1, newDoc2] });
      expect(wrapper.find(FileCard)).toHaveLength(2);
    });

    describe("when there are additional files selected", () => {
      it("renders a FileCard for the old and new files", () => {
        const newFile = makeFileObject({ id: "newFile" });
        const wrapper = render({
          tempFiles: new TempFileCollection([newFile]),
          documents: [newDoc1, newDoc2],
        });
        expect(wrapper.find(FileCard)).toHaveLength(3);
      });

      it("continues numbering of the new FileCards from where it left off", () => {
        const newFiles = new TempFileCollection([
          makeFileObject({ id: "newFile1" }),
          makeFileObject({ id: "newFile2" }),
          makeFileObject({ id: "newFile3" }),
        ]);
        const wrapper = render({
          tempFiles: newFiles,
          documents: [newDoc1, newDoc2],
        });

        expect(wrapper.find(FileCard).last().prop("heading")).toBe(
          "Document 5"
        );
      });
    });
  });
});

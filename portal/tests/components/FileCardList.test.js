import { makeFile, testHook } from "../test-utils";
import Document from "../../src/models/Document";
import FileCard from "../../src/components/FileCard";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import TempFile from "../../src/models/TempFile";
import TempFileCollection from "../../src/models/TempFileCollection";
import { ValidationError } from "../../src/errors";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import tracker from "../../src/services/tracker";
import useCollectionState from "../../src/hooks/useCollectionState";

jest.mock("../../src/services/tracker");

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
        onAddTempFiles: jest.fn(),
        onInvalidFilesError: jest.fn(),
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

  it("calls onRemoveTempFile when user clicks remove file", () => {
    const initialFiles = new TempFileCollection([makeFileObject()]);
    let removeTempFile, tempFiles;
    testHook(() => {
      ({
        collection: tempFiles,
        removeItem: removeTempFile,
      } = useCollectionState(initialFiles));
    });

    const removeTempFileMock = jest
      .fn()
      .mockImplementation((id) => removeTempFile(id));

    act(() => {
      const wrapper = render({
        tempFiles,
        onRemoveTempFile: removeTempFileMock,
      });
      wrapper.find("FileCard").simulate("removeClick");
    });
    expect(removeTempFileMock).toHaveBeenCalledWith(initialFiles.items[0].id);
    expect(tempFiles.items).toEqual([]);
  });

  describe("when the user selects file(s)", () => {
    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("calls onAddTempFiles with a single file when the user selects a single file", () => {
      const initialFiles = new TempFileCollection([
        makeFileObject({ name: "file-1.png" }),
      ]);
      const newFile = makeFile({ name: "file-2.png" });

      let addFiles, tempFiles;
      testHook(() => {
        ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
          initialFiles
        ));
      });

      const addFilesMock = jest
        .fn()
        .mockImplementation((files) => addFiles(files));

      act(() => {
        const wrapper = render({ tempFiles, onAddTempFiles: addFilesMock });
        // simulate the user selecting a single file
        const input = wrapper.find("input");
        input.simulate("change", {
          target: {
            files: [newFile],
          },
        });
      });

      expect(addFilesMock).toHaveBeenCalledWith([
        expect.objectContaining({
          id: expect.any(String),
          file: expect.objectContaining({ name: "file-2.png" }),
        }),
      ]);

      expect(tempFiles.items.map((file) => file.file.name)).toEqual([
        "file-1.png",
        "file-2.png",
      ]);
    });

    it("calls onAddTempFiles with multiple files when the user selects multiple files", () => {
      const initialFiles = new TempFileCollection([
        makeFileObject({ name: "file-1.png" }),
      ]);
      const newFiles = [
        makeFileObject({ name: "file-2.png" }),
        makeFileObject({ name: "file-3.png" }),
      ];

      let addFiles, tempFiles;
      testHook(() => {
        ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
          initialFiles
        ));
      });

      const addFilesMock = jest
        .fn()
        .mockImplementation((files) => addFiles(files));

      act(() => {
        const wrapper = render({ tempFiles, onAddTempFiles: addFilesMock });
        // simulate the user selecting multiple files
        const input = wrapper.find("input");
        input.simulate("change", {
          target: {
            files: newFiles.map((file) => file.file),
          },
        });
      });

      expect(addFilesMock).toHaveBeenCalledWith([
        expect.objectContaining({
          id: expect.any(String),
          file: expect.objectContaining({ name: "file-2.png" }),
        }),
        expect.objectContaining({
          id: expect.any(String),
          file: expect.objectContaining({ name: "file-3.png" }),
        }),
      ]);

      expect(tempFiles.items.map((file) => file.file.name)).toEqual([
        "file-1.png",
        "file-2.png",
        "file-3.png",
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

    describe("when the user selects disallowed files", () => {
      describe("when the file is not allowed because of the file type", () => {
        let addFilesMock,
          handleInvalidFilesError,
          initialFiles,
          tempFiles,
          validFile;
        beforeEach(() => {
          let addFiles;
          initialFiles = new TempFileCollection([
            makeFileObject({ name: "file-1.png" }),
          ]);
          handleInvalidFilesError = jest.fn();
          validFile = makeFileObject({
            name: "valid-file.pdf",
            type: "application/pdf",
          });
          const invalidFile = makeFileObject({
            name: "invalid-file.exe",
            type: "application/exe",
          });

          testHook(() => {
            ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
              initialFiles
            ));
          });

          addFilesMock = jest
            .fn()
            .mockImplementation((files) => addFiles(files));

          act(() => {
            const wrapper = render({
              tempFiles,
              onAddTempFiles: addFilesMock,
              onInvalidFilesError: handleInvalidFilesError,
            });
            // simulate the user selecting files, including an invalid one
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });
        });

        it("filters out invalid files based on type", () => {
          expect(addFilesMock).toHaveBeenCalledWith([
            expect.objectContaining({
              id: expect.any(String),
              file: expect.objectContaining({ name: "valid-file.pdf" }),
            }),
          ]);
          expect(tempFiles.items.map((file) => file.file.name)).toEqual([
            "file-1.png",
            "valid-file.pdf",
          ]);
        });

        it("calls onInvalidFilesError handler", () => {
          const error = handleInvalidFilesError.mock.calls[0][0];
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues).toMatchInlineSnapshot(`
            Array [
              Object {
                "message": "We could not upload: invalid-file.exe. Choose a PDF or an image file (.jpg, .jpeg, .png).",
              },
            ]
          `);
        });

        it("tracks the error event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "FileValidationError",
            expect.any(Object)
          );
        });
      });
      describe("when the file is not allowed because of the file size", () => {
        let addFilesMock,
          handleInvalidFilesError,
          initialFiles,
          tempFiles,
          validFile;
        beforeEach(() => {
          let addFiles;
          handleInvalidFilesError = jest.fn();
          initialFiles = new TempFileCollection([
            makeFileObject({ name: "file-1.png" }),
          ]);
          validFile = makeFileObject({
            name: "valid-file.pdf",
            type: "application/pdf",
          });
          const invalidFile = makeFileObject({
            name: "invalid-file.pdf",
            type: "application/pdf",
          });
          Object.defineProperty(invalidFile.file, "size", {
            get: () => 3500001,
          });
          testHook(() => {
            ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
              initialFiles
            ));
          });

          addFilesMock = jest
            .fn()
            .mockImplementation((files) => addFiles(files));

          act(() => {
            const wrapper = render({
              tempFiles,
              onAddTempFiles: addFilesMock,
              onInvalidFilesError: handleInvalidFilesError,
            });
            // simulate the user selecting files, including the invalid file
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });
        });

        it("filters out invalid files based on size", () => {
          expect(addFilesMock).toHaveBeenCalledWith([
            expect.objectContaining({
              id: expect.any(String),
              file: expect.objectContaining({ name: "valid-file.pdf" }),
            }),
          ]);
          expect(tempFiles.items.map((file) => file.file.name)).toEqual([
            "file-1.png",
            "valid-file.pdf",
          ]);
        });

        it("calls onInvalidFilesError handler", () => {
          const error = handleInvalidFilesError.mock.calls[0][0];
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues).toMatchInlineSnapshot(`
            Array [
              Object {
                "message": "We could not upload: invalid-file.pdf. Files must be smaller than 3.5 MB.",
              },
            ]
          `);
        });

        it("tracks the error event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "FileValidationError",
            expect.any(Object)
          );
        });
      });

      describe("when the file is not allowed because of file type and size", () => {
        let addFilesMock,
          handleInvalidFilesError,
          initialFiles,
          tempFiles,
          validFile;
        beforeEach(() => {
          let addFiles;
          handleInvalidFilesError = jest.fn();
          initialFiles = new TempFileCollection([
            makeFileObject({ name: "file-1.png" }),
          ]);
          validFile = makeFileObject({
            name: "valid-file.pdf",
            type: "application/pdf",
          });
          const invalidFile = makeFileObject({
            name: "invalid-file.exe",
            type: "application/exe",
          });
          Object.defineProperty(invalidFile.file, "size", {
            get: () => 3500001,
          });
          testHook(() => {
            ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
              initialFiles
            ));
          });

          addFilesMock = jest
            .fn()
            .mockImplementation((files) => addFiles(files));

          act(() => {
            const wrapper = render({
              tempFiles,
              onAddTempFiles: addFilesMock,
              onInvalidFilesError: handleInvalidFilesError,
            });
            // simulate the user selecting files, including the invalid file
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });
        });

        it("filters out invalid files based on type and size", () => {
          expect(addFilesMock).toHaveBeenCalledWith([
            expect.objectContaining({
              id: expect.any(String),
              file: expect.objectContaining({ name: "valid-file.pdf" }),
            }),
          ]);
          expect(tempFiles.items.map((file) => file.file.name)).toEqual([
            "file-1.png",
            "valid-file.pdf",
          ]);
        });

        it("calls onInvalidFilesError handler", () => {
          const error = handleInvalidFilesError.mock.calls[0][0];
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues).toMatchInlineSnapshot(`
            Array [
              Object {
                "message": "We could not upload: invalid-file.exe. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 3.5 MB.",
              },
            ]
          `);
        });

        it("tracks the error event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "FileValidationError",
            expect.any(Object)
          );
        });
      });

      describe("when files are invalid for multiple reasons", () => {
        let addFilesMock, handleInvalidFilesError, tempFiles, wrapper;
        beforeEach(() => {
          let addFiles;
          handleInvalidFilesError = jest.fn();
          const invalidTypeFiles = [
            makeFile({ name: "type1.exe", type: "application/exe" }),
            makeFile({ name: "type2.gif", type: "image/gif" }),
          ];
          const invalidSizeFiles = [
            makeFile({ name: "size1.pdf", type: "application/pdf" }),
            makeFile({ name: "size2.pdf", type: "application/pdf" }),
          ];

          invalidSizeFiles.forEach((file) =>
            Object.defineProperty(file, "size", { get: () => 3500001 })
          );
          const invalidSizeAndTypeFiles = [
            makeFile({ name: "sizeAndType1.exe", type: "application/exe" }),
            makeFile({ name: "sizeAndType2.gif", type: "application/gif" }),
          ];
          invalidSizeAndTypeFiles.forEach((file) =>
            Object.defineProperty(file, "size", { get: () => 3500001 })
          );

          testHook(() => {
            ({ collection: tempFiles, addItems: addFiles } = useCollectionState(
              new TempFileCollection()
            ));
          });

          addFilesMock = jest
            .fn()
            .mockImplementation((files) => addFiles(files));

          act(() => {
            wrapper = render({
              tempFiles,
              onAddTempFiles: addFilesMock,
              onInvalidFilesError: handleInvalidFilesError,
            });
            wrapper.find("input").simulate("change", {
              target: {
                files: [
                  ...invalidTypeFiles,
                  ...invalidSizeFiles,
                  ...invalidSizeAndTypeFiles,
                ],
              },
            });
          });
        });

        it("filters out invalid files based on type and size", () => {
          expect(addFilesMock).toHaveBeenCalledWith([]);
          expect(tempFiles.items).toEqual([]);
        });

        it("calls onInvalidFilesError handler", () => {
          const error = handleInvalidFilesError.mock.calls[0][0];
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues).toMatchInlineSnapshot(`
            Array [
              Object {
                "message": "We could not upload: type1.exe. Choose a PDF or an image file (.jpg, .jpeg, .png).",
              },
              Object {
                "message": "We could not upload: type2.gif. Choose a PDF or an image file (.jpg, .jpeg, .png).",
              },
              Object {
                "message": "We could not upload: size1.pdf. Files must be smaller than 3.5 MB.",
              },
              Object {
                "message": "We could not upload: size2.pdf. Files must be smaller than 3.5 MB.",
              },
              Object {
                "message": "We could not upload: sizeAndType1.exe. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 3.5 MB.",
              },
              Object {
                "message": "We could not upload: sizeAndType2.gif. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 3.5 MB.",
              },
            ]
          `);
        });

        it("tracks the event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledTimes(6);
        });
      });
    });
  });

  describe("with documents in props", () => {
    const mock_application_id = "mock_application_id";
    let newDoc1, newDoc2;
    beforeEach(() => {
      newDoc1 = new Document({
        document_type: DocumentType.medicalCertification,
        application_id: mock_application_id,
        fineos_document_id: "testId1",
        created_at: "2020-11-26",
      });
      newDoc2 = new Document({
        document_type: DocumentType.medicalCertification,
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

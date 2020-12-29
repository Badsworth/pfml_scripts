import React, { useState } from "react";
import _, { uniqueId } from "lodash";
import { makeFile, testHook } from "../test-utils";
import Document from "../../src/models/Document";
import FileCard from "../../src/components/FileCard";
import FileCardList from "../../src/components/FileCardList";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import tracker from "../../src/services/tracker";

jest.mock("../../src/services/tracker");

const makeFileObject = (attrs = {}) => {
  const { id, type } = Object.assign(
    {
      id: uniqueId("File"),
      type: "application/pdf",
    },
    attrs
  );

  const name = attrs.name || `${id}.pdf`;

  const file = makeFile({ name, type });
  return { id, file };
};

describe("FileCardList", () => {
  function render(customProps = {}) {
    const props = Object.assign(
      {
        filesWithUniqueId: [],
        fileErrors: [],
        setFiles: jest.fn(),
        appErrors: [],
        setAppErrors: jest.fn(),
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
    const filesWithUniqueId = [makeFileObject()];

    it("renders a list of the files", () => {
      const wrapper = render({ filesWithUniqueId });

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the 'Add another file' button text", () => {
      const addAnotherFileButtonText = "Choose more files!";
      const wrapper = render({ filesWithUniqueId, addAnotherFileButtonText });

      expect(wrapper.find("label").text()).toBe(addAnotherFileButtonText);
    });
  });

  it("removes a file when the remove handler is called", () => {
    const initialFiles = [makeFileObject()];
    let files, setFiles;
    testHook(() => {
      [files, setFiles] = useState(initialFiles);
    });
    act(() => {
      const wrapper = render({ filesWithUniqueId: files, setFiles });
      wrapper.find("FileCard").simulate("removeClick");
    });
    expect(files).toEqual([]);
  });

  describe("when the user selects file(s)", () => {
    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("adds a single file when the user selects a single file", () => {
      const initialFiles = [makeFileObject()];
      const id = "FileX";
      const newFile = makeFileObject({ id });
      jest.spyOn(_, "uniqueId").mockImplementationOnce(() => id);

      let files, setFiles;
      testHook(() => {
        [files, setFiles] = useState(initialFiles);
      });

      act(() => {
        const wrapper = render({ files, setFiles });
        // simulate the user selecting a single file
        const input = wrapper.find("input");
        input.simulate("change", {
          target: {
            files: [newFile.file],
          },
        });
      });

      expect(files).toEqual([...initialFiles, newFile]);
    });

    it("adds multiple files when the user selects multiple files", () => {
      const initialFiles = [makeFileObject()];
      const id = "FileX";
      const newFiles = [makeFileObject({ id }), makeFileObject({ id })];
      jest.spyOn(_, "uniqueId").mockImplementation(() => id);

      let files, setFiles;
      testHook(() => {
        [files, setFiles] = useState(initialFiles);
      });

      act(() => {
        const wrapper = render({ files, setFiles });
        // simulate the user selecting multiple files
        const input = wrapper.find("input");
        input.simulate("change", {
          target: {
            files: newFiles.map((file) => file.file),
          },
        });
      });

      expect(files).toEqual([...initialFiles, ...newFiles]);
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
        it("filters out invalid files based on type", () => {
          const initialFiles = [makeFileObject()];
          const id = "FileX";
          const validFile = makeFileObject({ id, type: "application/pdf" });
          const invalidFile = makeFileObject({ id, type: "application/exe" });
          jest.spyOn(_, "uniqueId").mockImplementation(() => id);

          let files, setFiles, wrapper;
          testHook(() => {
            [files, setFiles] = useState(initialFiles);
          });

          act(() => {
            wrapper = render({ files, setFiles });
            // simulate the user selecting files, including an invalid one
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });

          expect(files).toEqual([...initialFiles, validFile]);
        });

        it("displays an AppError message for file with invalid type", () => {
          const invalidFile = makeFile({
            name: "file.exe",
            type: "application/exe",
          });

          let appErrors, setAppErrors, wrapper;
          testHook(() => {
            [appErrors, setAppErrors] = useState([]);
          });

          act(() => {
            wrapper = render({ appErrors, setAppErrors });
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(appErrors.items).toHaveLength(1);
          expect(appErrors.items[0].message).toMatchInlineSnapshot(
            `"We could not upload: file.exe. Choose a PDF or an image file (.jpg, .jpeg, .png)."`
          );
        });

        it("tracks the error event", () => {
          const invalidFile = makeFile({
            name: "file.exe",
            type: "application/exe",
          });

          act(() => {
            const wrapper = render();
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "ValidationError",
            expect.any(Object)
          );
        });
      });
      describe("when the file is not allowed because of the file size", () => {
        it("filters out invalid files based on size", () => {
          const initialFiles = [makeFileObject()];
          const id = "FileX";
          const validFile = makeFileObject({ id, type: "application/pdf" });
          const invalidFile = makeFileObject({ id, type: "application/pdf" });
          Object.defineProperty(invalidFile.file, "size", {
            get: () => 3500001,
          });
          jest.spyOn(_, "uniqueId").mockImplementation(() => id);

          let files, setFiles, wrapper;
          testHook(() => {
            [files, setFiles] = useState(initialFiles);
          });

          act(() => {
            wrapper = render({ files, setFiles });
            // simulate the user selecting files, including the invalid file
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });

          expect(files).toEqual([...initialFiles, validFile]);
        });

        it("displays an AppError message for the file with invalid size", () => {
          const invalidFile = makeFile({
            name: "file.pdf",
            type: "application/pdf",
          });
          Object.defineProperty(invalidFile, "size", {
            get: () => 3500001,
          });

          let appErrors, setAppErrors, wrapper;
          testHook(() => {
            [appErrors, setAppErrors] = useState([]);
          });

          act(() => {
            wrapper = render({ appErrors, setAppErrors });
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(appErrors.items).toHaveLength(1);
          expect(appErrors.items[0].message).toMatchInlineSnapshot(
            `"We could not upload: file.pdf. Files must be smaller than 3.5 MB."`
          );
        });
        it("tracks the error event", () => {
          const invalidFile = makeFile({
            name: "file.pdf",
            type: "application/pdf",
          });
          Object.defineProperty(invalidFile, "size", {
            get: () => 3500001,
          });

          act(() => {
            const wrapper = render();
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "ValidationError",
            expect.any(Object)
          );
        });
      });
      describe("when the file is not allowed because of file type and size", () => {
        it("filters out invalid files based on type and size", () => {
          const initialFiles = [makeFileObject()];
          const id = "FileX";
          const validFile = makeFileObject({ id, type: "application/pdf" });
          const invalidFile = makeFileObject({ id, type: "application/exe" });
          Object.defineProperty(invalidFile.file, "size", {
            get: () => 3500001,
          });
          jest.spyOn(_, "uniqueId").mockImplementation(() => id);

          let files, setFiles, wrapper;
          testHook(() => {
            [files, setFiles] = useState(initialFiles);
          });

          act(() => {
            wrapper = render({ files, setFiles });
            // simulate the user selecting files, including the invalid file
            const input = wrapper.find("input");
            input.simulate("change", {
              target: {
                files: [validFile.file, invalidFile.file],
              },
            });
          });

          expect(files).toEqual([...initialFiles, validFile]);
        });

        it("displays an AppError message for the file with invalid type and size", () => {
          const invalidFile = makeFile({
            name: "file.exe",
            type: "application/exe",
          });
          Object.defineProperty(invalidFile, "size", {
            get: () => 3500001,
          });

          let appErrors, setAppErrors, wrapper;
          testHook(() => {
            [appErrors, setAppErrors] = useState([]);
          });

          act(() => {
            wrapper = render({ appErrors, setAppErrors });
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(appErrors.items).toHaveLength(1);
          expect(appErrors.items[0].message).toMatchInlineSnapshot(
            `"We could not upload: file.exe. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 3.5 MB."`
          );
        });
        it("tracks the error event", () => {
          const invalidFile = makeFile({
            name: "file.exe",
            type: "application/exe",
          });
          Object.defineProperty(invalidFile, "size", {
            get: () => 3500001,
          });

          act(() => {
            const wrapper = render();
            wrapper.find("input").simulate("change", {
              target: {
                files: [invalidFile],
              },
            });
          });

          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "ValidationError",
            expect.any(Object)
          );
        });
      });
      describe("when files are invalid for multiple reasons", () => {
        it("displays an AppError for each reason", () => {
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

          let appErrors, setAppErrors, wrapper;
          testHook(() => {
            [appErrors, setAppErrors] = useState([]);
          });

          act(() => {
            wrapper = render({ appErrors, setAppErrors });
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

          expect(appErrors.items).toHaveLength(3);
          expect(appErrors.items.map((item) => item.message))
            .toMatchInlineSnapshot(`
            Array [
              "We could not upload: size1.pdf, size2.pdf. Files must be smaller than 3.5 MB.",
              "We could not upload: type1.exe, type2.gif. Choose a PDF or an image file (.jpg, .jpeg, .png).",
              "We could not upload: sizeAndType1.exe, sizeAndType2.gif. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 3.5 MB.",
            ]
          `);
        });
        it("tracks the event", () => {
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

          let appErrors, setAppErrors, wrapper;
          testHook(() => {
            [appErrors, setAppErrors] = useState([]);
          });

          act(() => {
            wrapper = render({ appErrors, setAppErrors });
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
          filesWithUniqueId: [newFile],
          documents: [newDoc1, newDoc2],
        });
        expect(wrapper.find(FileCard)).toHaveLength(3);
      });

      it("continues numbering of the new FileCards from where it left off", () => {
        const newFiles = [
          makeFileObject({ id: "newFile1" }),
          makeFileObject({ id: "newFile2" }),
          makeFileObject({ id: "newFile3" }),
        ];
        const wrapper = render({
          filesWithUniqueId: newFiles,
          documents: [newDoc1, newDoc2],
        });

        expect(wrapper.find(FileCard).last().prop("heading")).toBe(
          "Document 5"
        );
      });
    });
  });
});

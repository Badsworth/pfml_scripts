import React, { useState } from "react";
import _, { uniqueId } from "lodash";
import { makeFile, testHook } from "../test-utils";
import FileCardList from "../../src/components/FileCardList";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";

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
        files: [],
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
    const files = [makeFileObject()];

    it("renders a list of the files", () => {
      const wrapper = render({ files });

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the 'Add another file' button text", () => {
      const addAnotherFileButtonText = "Choose more files!";
      const wrapper = render({ files, addAnotherFileButtonText });

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
      const wrapper = render({ files, setFiles });
      wrapper.find("FileCard").simulate("removeClick");
    });
    expect(files).toEqual([]);
  });

  describe("when the user selects file(s)", () => {
    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("adds a single file when the user selects a single file", async () => {
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

    it("filters out invalid files", () => {
      const initialFiles = [makeFileObject()];
      const id = "FileX";
      const validFile = makeFileObject({ id });
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

    it("sets page errors for each invalid file the user selects", () => {
      const invalidFileName = "file.exe";
      const invalidFile = makeFile({
        name: invalidFileName,
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
        `"Only PDF and image files may be uploaded. See the tips below for suggestions on how to convert them to an image file. These files that you selected will not be uploaded: ${invalidFileName}"`
      );
    });
  });

  it.todo("sets page errors for each invalid file the user selects");
});

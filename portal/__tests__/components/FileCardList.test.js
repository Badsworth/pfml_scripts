import _, { uniqueId } from "lodash";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import { shallow } from "enzyme";

const makeFile = (attrs = {}) => {
  const { id, type } = Object.assign(
    {
      id: uniqueId("File"),
      type: "application/pdf",
    },
    attrs
  );

  const name = attrs.name || `${id}.pdf`;

  const file = new File([], name, { type });
  return { id, file };
};

function render(customProps = {}) {
  const props = Object.assign(
    {
      files: [],
      setFiles: jest.fn(),
      fileHeadingPrefix: "Document",
      addFirstFileButtonText: "Choose a document",
      addAnotherFileButtonText: "Choose another document",
    },
    customProps
  );

  const fileCardList = <FileCardList {...props} />;

  return shallow(fileCardList);
}

describe("FileCardList", () => {
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
    const files = [makeFile()];

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
    const file = makeFile();
    const files = [file];
    let updatedFiles;
    const setFiles = jest.fn((callback) => (updatedFiles = callback(files)));
    const wrapper = render({ files, setFiles });
    // Find the file card and dive() into its wrapper
    const fileCard = wrapper.find("FileCard");
    // Simulate the "Remove document" button being clicked
    fileCard.simulate("removeClick");

    expect(setFiles).toHaveBeenCalled();
    expect(updatedFiles).toEqual([]);
  });

  describe("when the user selects file(s)", () => {
    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("adds a single file when the user selects a single file", () => {
      const files = [makeFile()];
      let updatedFiles;
      const setFiles = jest.fn((callback) => (updatedFiles = callback(files)));
      const wrapper = render({ files, setFiles });
      const input = wrapper.find("input");

      // simulate the user selecting a single file
      const newFile = new File([], "file.pdf", { type: "application/pdf" });
      const id = "File1";
      jest.spyOn(_, "uniqueId").mockImplementationOnce(() => id);
      input.simulate("change", {
        target: {
          files: [newFile],
        },
      });

      const expectedFiles = [...files, { id, file: newFile }];
      expect(setFiles).toHaveBeenCalled();
      expect(updatedFiles).toEqual(expectedFiles);
    });

    it("adds multiple files when the user selects multiple files", () => {
      const files = [makeFile()];
      let updatedFiles;
      const setFiles = jest.fn((callback) => (updatedFiles = callback(files)));
      const wrapper = render({ files, setFiles });
      const input = wrapper.find("input");

      // simulate the user selecting multiple files
      const file = new File([], "file.pdf", { type: "application/pdf" });
      const id = "File1";
      jest.spyOn(_, "uniqueId").mockImplementation(() => id);
      input.simulate("change", {
        target: {
          files: [file, file],
        },
      });

      const expectedFiles = [...files, { id, file }, { id, file }];
      expect(setFiles).toHaveBeenCalled();
      expect(updatedFiles).toEqual(expectedFiles);
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
      const newFile = new File([], "file.pdf", { type: "application/pdf" });

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
      const files = [makeFile()];
      let updatedFiles;
      const setFiles = jest.fn((callback) => (updatedFiles = callback(files)));
      const wrapper = render({ files, setFiles });
      const input = wrapper.find("input");

      // simulate the user selecting multiple files
      const validFile = new File([], "file.pdf", { type: "application/pdf" });
      const invalidFile = new File([], "file.exe", { type: "application/exe" });
      const id = "File1";
      jest.spyOn(_, "uniqueId").mockImplementation(() => id);
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      input.simulate("change", {
        target: {
          files: [validFile, invalidFile],
        },
      });

      const expectedFiles = [...files, { id, file: validFile }];
      expect(setFiles).toHaveBeenCalled();
      expect(updatedFiles).toEqual(expectedFiles);
    });
  });

  it.todo("sets page errors for each invalid file the user selects");
});

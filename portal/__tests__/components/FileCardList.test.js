import _, { uniqueId } from "lodash";
import FileCardList from "../../src/components/FileCardList";
import React from "react";
import { shallow } from "enzyme";

function makeFile() {
  const id = uniqueId("File");
  const file = new File([], `${id}.pdf`, { type: "application/pdf" });
  return { id, file };
}

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

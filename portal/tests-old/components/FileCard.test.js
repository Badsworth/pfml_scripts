import Document from "../../src/models/Document";
import FileCard from "../../src/components/FileCard";
import React from "react";
import { shallow } from "enzyme";

function render(props) {
  return shallow(<FileCard {...props} />);
}

describe("FileCard", () => {
  describe("when the FileCard receives a File", () => {
    const file = new File(["foo"], "foo.png", { type: "image/png" });
    const props = {
      heading: "Document 1",
      file,
      onRemoveClick: jest.fn(),
    };

    it("renders", () => {
      const wrapper = render(props);
      expect(wrapper).toMatchSnapshot();
    });

    it("calls the onRemoveClick handler when the remove button is clicked", () => {
      const wrapper = render(props);
      wrapper.find("Button").simulate("click");
      expect(props.onRemoveClick).toHaveBeenCalledTimes(1);
    });

    it("renders the error message", () => {
      const wrapper = render({ ...props, errorMsg: "error" });
      expect(wrapper.find("p.text-error")).toMatchSnapshot();
    });
  });

  describe("when the FileCard receives a Document", () => {
    const props = {
      document: new Document({ created_at: "2020-11-26" }),
      heading: "Document 1",
    };
    it("renders a FileCard component without a Button", () => {
      const wrapper = render(props);
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("Button").exists()).toBe(false);
    });

    it("displays the date uploaded", () => {
      const wrapper = render(props);
      expect(wrapper.find(".c-file-card__name").text()).toBe(
        "Date of upload: 11/26/2020"
      );
    });
  });
});

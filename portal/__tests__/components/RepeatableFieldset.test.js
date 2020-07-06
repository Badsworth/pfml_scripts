import { mount, shallow } from "enzyme";
import React from "react";
import RepeatableFieldset from "../../src/components/RepeatableFieldset";
import { act } from "react-dom/test-utils";

describe("RepeatableFieldset", () => {
  let props;

  beforeEach(() => {
    props = {
      addButtonLabel: "Remove",
      entries: [{ first_name: "Anton" }, { first_name: "Bud" }],
      render: (entry, index) => (
        <p>
          {entry.first_name} – {index}
        </p>
      ),
      headingPrefix: "Person",
      removeButtonLabel: "Remove",
      onAddClick: jest.fn(),
      onRemoveClick: jest.fn(),
    };
  });

  it("renders a RepeatableFieldsetCard for each entry", () => {
    const wrapper = shallow(<RepeatableFieldset {...props} />);

    expect(wrapper).toMatchSnapshot();
  });

  describe("given only one entry exists", () => {
    it("does not show a Remove button", () => {
      props.entries = [{ first_name: "Bud" }];

      const wrapper = shallow(<RepeatableFieldset {...props} />);

      expect(
        wrapper.find("RepeatableFieldsetCard").prop("showRemoveButton")
      ).toBe(false);
    });
  });

  describe("when the add button is clicked", () => {
    it("calls onAddClick", () => {
      const wrapper = shallow(<RepeatableFieldset {...props} />);
      const addButton = wrapper.find("Button").last();

      addButton.simulate("click");

      expect(props.onAddClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("when a new entry is added", () => {
    it("changes the focused element to the last card's label", () => {
      // Hide warning about rendering in the body, since we need to for this test
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

      // Note: normally a tabIndex isn't needed on labels, but it is for JS DOM:
      /* eslint-disable jsx-a11y/no-noninteractive-tabindex */
      props.render = () => (
        <label className="test-label" htmlFor="field" tabIndex="0">
          Hello
        </label>
      );

      // Use `mount` so that useEffect and DOM selectors work
      const wrapper = mount(<RepeatableFieldset {...props} />, {
        // attachTo the body so document.activeElement works (https://github.com/enzymejs/enzyme/issues/2337#issuecomment-608984530)
        attachTo: document.body,
      });

      act(() => {
        // Pass in a longer list of entries
        const newEntries = props.entries.concat([{ first_name: "Charles" }]);
        wrapper.setProps({ entries: newEntries });
      });

      const label = wrapper.find(".test-label").last().getDOMNode();

      expect(document.activeElement).toBe(label);
    });
  });

  describe("when an entry is removed", () => {
    it("changes the RepeatableFieldsetCard key", () => {
      // Use `mount` so that useEffect works
      const wrapper = mount(<RepeatableFieldset {...props} />);
      const initialKey = wrapper.find("RepeatableFieldsetCard").first().key();

      act(() => {
        const newEntries = [].concat(props.entries);
        newEntries.pop();
        wrapper.setProps({ entries: newEntries });
      });

      // Hack to wait for the setState to be called after the effect is triggered above
      // Forces a re-render
      act(() => {
        wrapper.setProps({});
      });

      const newKey = wrapper.find("RepeatableFieldsetCard").first().key();

      expect(initialKey).toBeDefined();
      expect(newKey).toBeDefined();
      expect(newKey).not.toEqual(initialKey);
    });
  });
});

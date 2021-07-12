import { mount, shallow } from "enzyme";
import React from "react";
import RepeatableFieldset from "../../src/components/RepeatableFieldset";
import { act } from "react-dom/test-utils";

describe("RepeatableFieldset", () => {
  let props, wrapper;

  beforeEach(() => {
    props = {
      addButtonLabel: "Remove",
      entries: [
        { first_name: "Anton" },
        { first_name: "Bud" },
        { first_name: "Cat" },
      ],
      // eslint-disable-next-line react/display-name
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
    act(() => {
      wrapper = shallow(<RepeatableFieldset {...props} />);
    });
    expect(wrapper).toMatchSnapshot();
  });

  describe("when a limit is set", () => {
    it("shows an enabled add button without limit message when limit is not reached", () => {
      props.entries = [{ first_name: "Bud" }];
      props.limit = 2;
      props.limitMessage = "You can only add 2";

      const wrapper = shallow(<RepeatableFieldset {...props} />);
      const addButton = wrapper.find("Button").last();
      const limitMessage = wrapper.find("Button + strong");

      expect(addButton.prop("disabled")).toBe(false);
      expect(limitMessage.exists()).toBe(false);
    });

    it("shows disabled add button and limit message when the limit is reached", () => {
      props.entries = [{ first_name: "Bud" }, { first_name: "Scooter" }];
      props.limit = 2;
      props.limitMessage = "You can only add 2";

      const wrapper = shallow(<RepeatableFieldset {...props} />);
      const addButton = wrapper.find("Button").last();
      const limitMessage = wrapper.find("Button + strong").text();

      expect(addButton.prop("disabled")).toBe(true);
      expect(limitMessage).toMatchInlineSnapshot(`"You can only add 2"`);
    });
  });

  describe("given only one entry exists", () => {
    it("does not show a Remove button", () => {
      props.entries = [{ first_name: "Bud" }];

      act(() => {
        // useEffect doesn't work with enzyme's shallow function
        // see https://github.com/enzymejs/enzyme/issues/2086 and https://github.com/enzymejs/enzyme/issues/2011
        wrapper = mount(<RepeatableFieldset {...props} />);
      });
      // Need to call wrapper.update since updates were made outside
      // of the act call as part of the useEffect callback
      wrapper.update();

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
      // eslint-disable-next-line react/display-name
      props.render = () => (
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
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
      // Need to call wrapper.update since updates were made outside
      // of the act call as part of the useEffect callback
      wrapper.update();

      const label = wrapper.find(".test-label").last().getDOMNode();

      expect(document.activeElement).toBe(label);
    });
  });

  describe("when an entry is removed", () => {
    it("keeps RepeatableFieldsetCard keys stable", () => {
      const { entries } = props;
      // Use `mount` so that useEffect works
      // see https://github.com/enzymejs/enzyme/issues/2086 and https://github.com/enzymejs/enzyme/issues/2011
      act(() => {
        wrapper = mount(<RepeatableFieldset {...props} />);
      });
      // Need to call wrapper.update since updates were made outside
      // of the act call as part of the useEffect callback
      wrapper.update();

      const keys1 = wrapper
        .find("RepeatableFieldsetCard")
        .map((wrapper) => wrapper.key());

      act(() => {
        // Remove element at index 1
        const newEntries = entries.slice(0, 1).concat(entries.slice(2));
        wrapper.setProps({ entries: newEntries });
      });
      // Need to call wrapper.update since updates were made outside
      // of the act call as part of the useEffect callback
      wrapper.update();

      const keys2 = wrapper
        .find("RepeatableFieldsetCard")
        .map((wrapper) => wrapper.key());

      expect(keys2.length).toBe(keys1.length - 1);
      expect(keys2[0]).toBe(keys1[0]);
      expect(keys2.slice(1)).toEqual(keys1.slice(2));
    });
  });
});

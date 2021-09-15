import { act, render, screen } from "@testing-library/react";
import React from "react";
import RepeatableFieldset from "../../src/components/RepeatableFieldset";
import userEvent from "@testing-library/user-event";

const renderComponent = (customProps = {}) => {
  const props = {
    addButtonLabel: "Add",
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

  return render(<RepeatableFieldset {...props} {...customProps} />);
};

describe("RepeatableFieldset", () => {
  it("renders a RepeatableFieldsetCard for each entry", () => {
    const { container } = renderComponent();

    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows an enabled add button without limit message when limit is not reached", () => {
    const limitProps = {
      entries: [{ first_name: "Bud" }],
      limit: 2,
      limitMessage: "You can only add 2",
    };
    renderComponent(limitProps);

    const addButton = screen.getByRole("button");
    expect(addButton).not.toHaveAttribute("disabled");
    expect(screen.queryByText("You can only add 2")).toBeNull();
  });

  it("shows disabled add button and limit message when the limit is reached", () => {
    const limitProps = {
      entries: [{ first_name: "Bud" }, { first_name: "Scooter" }],
      limit: 2,
      limitMessage: "You can only add 2",
    };
    renderComponent(limitProps);

    const addButton = screen.getByRole("button", { name: "Add" });
    expect(addButton).toHaveAttribute("disabled");
    expect(screen.getByText("You can only add 2")).toBeInTheDocument();
  });

  it("does not show a Remove button when only one entry exists", () => {
    renderComponent({ entries: [{ first_name: "Bud" }] });

    expect(screen.queryByRole("button", { name: "Remove" })).toBeNull();
  });

  it("calls onAddClick when the add button is clicked", () => {
    const onAddClickMock = jest.fn();
    renderComponent({ onAddClick: onAddClickMock });
    const addButton = screen.getByRole("button", { name: "Add" });

    userEvent.click(addButton);

    expect(onAddClickMock).toHaveBeenCalledTimes(1);
  });

  it("changes the focused element to the last card's label when a new entry is added", () => {
    const customRender = () => (
      <label className="test-label" htmlFor="field" tabIndex="0">
        Hello
      </label>
    );

    const RepeatableFieldsetWithState = ({ initialEntries }) => {
      const [entries, setEntries] = React.useState(initialEntries);
      const handleAddClick = () => {
        const newEntries = entries.concat([{ first_name: "Dog" }]);
        setEntries(newEntries);
      };
      const props = {
        addButtonLabel: "Add",
        entries,
        // eslint-disable-next-line react/display-name
        render: customRender,
        headingPrefix: "Person",
        removeButtonLabel: "Remove",
        onAddClick: handleAddClick,
        onRemoveClick: jest.fn(),
      };

      return <RepeatableFieldset {...props} />;
    };

    render(
      <RepeatableFieldsetWithState initialEntries={[{ first_name: "Anton" }]} />
    );
    const addButton = screen.getByRole("button", { name: "Add" });
    userEvent.click(addButton);

    const [firstEntry, secondEntry] = screen.getAllByText("Hello");
    expect(firstEntry).not.toHaveFocus();
    expect(secondEntry).toHaveFocus();
  });

  describe.skip("when an entry is removed", () => {
    it("keeps RepeatableFieldsetCard keys stable when an entry is removed", () => {
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

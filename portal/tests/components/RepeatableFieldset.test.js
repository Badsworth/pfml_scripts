import { render, screen, within } from "@testing-library/react";
import React from "react";
import RepeatableFieldset from "../../src/components/RepeatableFieldset";
import userEvent from "@testing-library/user-event";

const defaultProps = {
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

const renderComponent = (customProps = {}) => {
  return render(<RepeatableFieldset {...defaultProps} {...customProps} />);
};

const RepeatableFieldsetWithState = ({ initialEntries }) => {
  const customRender = () => (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <label className="test-label" htmlFor="field" tabIndex="0">
      Hello
    </label>
  );
  const [entries, setEntries] = React.useState(initialEntries);
  const handleAddClick = () => {
    const updatedEntries = entries.concat([{ first_name: "Dog" }]);
    setEntries(updatedEntries);
  };
  const handleRemoveClick = (_entry, index) => {
    const updatedEntries = [...entries];
    updatedEntries.splice(index, 1);
    setEntries(updatedEntries);
  };
  const props = {
    ...defaultProps,
    entries,
    render: customRender,
    onAddClick: handleAddClick,
    onRemoveClick: handleRemoveClick,
  };

  return <RepeatableFieldset {...props} />;
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

    const addButton = screen.getByRole("button", { name: "Add" });
    expect(addButton).toBeEnabled();
    expect(screen.queryByText("You can only add 2")).not.toBeInTheDocument();
  });

  it("shows disabled add button and limit message when the limit is reached", () => {
    const limitProps = {
      entries: [{ first_name: "Bud" }, { first_name: "Scooter" }],
      limit: 2,
      limitMessage: "You can only add 2",
    };
    renderComponent(limitProps);

    const addButton = screen.getByRole("button", { name: "Add" });
    expect(addButton).toBeDisabled();
    expect(screen.getByText("You can only add 2")).toBeInTheDocument();
  });

  it("does not show a Remove button when only one entry exists", () => {
    renderComponent({ entries: [{ first_name: "Bud" }] });

    expect(
      screen.queryByRole("button", { name: "Remove" })
    ).not.toBeInTheDocument();
  });

  it("calls onAddClick when the add button is clicked", () => {
    const onAddClickMock = jest.fn();
    renderComponent({ onAddClick: onAddClickMock });
    const addButton = screen.getByRole("button", { name: "Add" });

    userEvent.click(addButton);

    expect(onAddClickMock).toHaveBeenCalledTimes(1);
  });

  it("changes the focused element to the last card's label when a new entry is added", () => {
    render(
      <RepeatableFieldsetWithState initialEntries={[{ first_name: "Anton" }]} />
    );
    const addButton = screen.getByRole("button", { name: "Add" });
    userEvent.click(addButton);

    const [firstEntry, secondEntry] = screen.getAllByText("Hello");
    expect(firstEntry).not.toHaveFocus();
    expect(secondEntry).toHaveFocus();
  });

  it("keeps RepeatableFieldsetCard keys stable when an entry is removed", () => {
    // we could not get `key` through RTL render, so we set the `data-key`attribute to check
    // if the keys stay the same.
    render(
      <RepeatableFieldsetWithState
        initialEntries={[{ first_name: "Anton" }, { first_name: "Bud" }]}
      />
    );
    const [firstEntry1, secondEntry1] = screen.getAllByTestId(
      "repeatable-fieldset-card"
    );

    const removeSecondEntryButton = within(secondEntry1).getByRole("button", {
      name: "Remove",
    });
    userEvent.click(removeSecondEntryButton);

    const [firstEntry2] = screen.getAllByTestId("repeatable-fieldset-card");
    expect(firstEntry2.attributes).toEqual(firstEntry1.attributes);
  });
});

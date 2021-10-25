import PreviousLeave, {
  PreviousLeaveReason,
  PreviousLeaveType,
} from "../../../src/models/PreviousLeave";
import { render, screen } from "@testing-library/react";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import PreviousLeaves from "../../../src/components/employers/PreviousLeaves";
import React from "react";
import { times } from "lodash";
import userEvent from "@testing-library/user-event";

const BASE_PREVIOUS_LEAVE = new PreviousLeave({
  is_for_current_employer: true,
  leave_minutes: 2400,
  leave_reason: PreviousLeaveReason.serviceMemberFamily,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
  previous_leave_id: 0,
  type: PreviousLeaveType.otherReason,
  worked_per_week_minutes: 1440,
});

const generatePreviousLeaves = (n = 1) =>
  times(
    n,
    (n) => new PreviousLeave({ ...BASE_PREVIOUS_LEAVE, previous_leave_id: n })
  );

describe("PreviousLeaves", () => {
  const onAdd = jest.fn();
  const onChange = jest.fn();
  const onRemove = jest.fn();

  const defaultProps = {
    addedPreviousLeaves: [],
    appErrors: new AppErrorInfoCollection(),
    onAdd,
    onChange,
    onRemove,
    previousLeaves: generatePreviousLeaves(),
    shouldShowV2: true,
  };

  const queryAmendmentFormHeader = () =>
    screen.queryByRole("heading", { name: /Amend previous leave/ });

  describe("when there are claimant-reported leaves", () => {
    it("shows a row for each leave", () => {
      const { container } = render(<PreviousLeaves {...defaultProps} />);
      expect(container).toMatchSnapshot();
    });

    it("allows for making amendments", () => {
      render(<PreviousLeaves {...defaultProps} />);

      userEvent.click(screen.getByRole("button", { name: /Amend/ }));

      expect(queryAmendmentFormHeader()).toBeInTheDocument();
    });

    it("allows for canceling amendments", () => {
      render(<PreviousLeaves {...defaultProps} />);
      userEvent.click(screen.getByRole("button", { name: /Amend/ }));

      userEvent.click(screen.getByRole("button", { name: /Cancel amendment/ }));

      expect(onChange).toHaveBeenCalled();
      expect(queryAmendmentFormHeader()).not.toBeInTheDocument();
    });
  });

  it("shows the fallback text when no claimant-reported leaves", () => {
    render(<PreviousLeaves {...defaultProps} previousLeaves={[]} />);
    expect(screen.queryByText(/None reported/)).toBeInTheDocument();
  });

  it('calls "onAdd" when the add button is clicked', () => {
    render(<PreviousLeaves {...defaultProps} />);

    userEvent.click(
      screen.getByRole("button", { name: /Add a previous leave/ })
    );

    expect(onAdd).toHaveBeenCalled();
  });

  describe("has a limit", () => {
    it("that restricts how many leaves can be added", () => {
      render(
        <PreviousLeaves
          {...defaultProps}
          addedPreviousLeaves={generatePreviousLeaves(4)}
        />
      );

      const addButton = screen.queryByRole("button", {
        name: /Add another previous leave/,
      });
      expect(addButton).toBeDisabled();
    });

    it("that is not affected by the number of claimant-submitted leaves", () => {
      render(
        <PreviousLeaves
          {...defaultProps}
          previousLeaves={generatePreviousLeaves(15)}
        />
      );

      const addButton = screen.queryByRole("button", {
        name: /Add a previous leave/,
      });
      expect(addButton).toBeEnabled();
    });
  });

  it('calls "onRemove" when the remove button is clicked for added amendments', () => {
    render(
      <PreviousLeaves
        {...defaultProps}
        previousLeaves={[]}
        addedPreviousLeaves={[BASE_PREVIOUS_LEAVE]}
      />
    );

    userEvent.click(screen.getByRole("button", { name: /Cancel addition/ }));

    expect(onRemove).toHaveBeenCalled();
  });
});

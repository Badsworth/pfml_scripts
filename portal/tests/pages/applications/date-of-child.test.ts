import BenefitsApplication, {
  ReasonQualifier,
} from "../../../src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "../../../src/models/ApiResourceCollection";
import DateOfChild from "../../../src/pages/applications/date-of-child";
import dayjs from "dayjs";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const past = dayjs().subtract(1, "month").format("YYYY-MM-DD");
const future = dayjs().add(1, "month").format("YYYY-MM-DD");

const setup = (claim = new MockBenefitsApplicationBuilder().create()) => {
  return renderPage(
    DateOfChild,
    {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.update = updateClaim;
        appLogic.benefitsApplications.benefitsApplications =
          new ApiResourceCollection<BenefitsApplication>("application_id", [
            claim,
          ]);
      },
    },
    { query: { claim_id: "mock_application_id" }, claim: {} }
  );
};

describe("DateOfChild", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("shows the birth date input with hint text when the claim is for a newborn", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();
    setup(claim);
    expect(
      screen.getByText(
        /If your child has not been born yet, enter the expected due date./
      )
    ).toBeInTheDocument();
  });

  it("shows the correct input question when the claim is for an adoption", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingAdoptionLeaveReason()
      .create();
    setup(claim);
    expect(
      screen.getByText(
        /When did the child arrive in your home through foster care or adoption?/
      )
    ).toBeInTheDocument();
  });

  describe("when child birth or placement date is in the future", () => {
    it("sets has_future_child_date as true for future birth bonding leave when claim is already populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason(future)
        .create();
      setup(claim);

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_birth_date: future,
            has_future_child_date: true,
          },
        });
      });
    });

    it("sets has_future_child_date as true for future birth bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.newBorn;

      setup(claim);
      const [year, month, day] = future.split("-");
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Month",
        }),
        month
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Day",
        }),
        day
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Year",
        }),
        year
      );

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_birth_date: future,
            has_future_child_date: true,
          },
        });
      });
    });

    it("sets has_future_child_date as true for future placement bonding leave when claim is already populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingFosterCareLeaveReason(future)
        .create();
      setup(claim);
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_placement_date: future,
            has_future_child_date: true,
          },
        });
      });
    });

    it("sets has_future_child_date as true for future placement bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.fosterCare;

      setup(claim);

      const [year, month, day] = future.split("-");
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Month",
        }),
        month
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Day",
        }),
        day
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Year",
        }),
        year
      );
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_placement_date: future,
            has_future_child_date: true,
          },
        });
      });
    });
  });

  describe("when child birth or placement date is in the past", () => {
    it("sets has_future_child_date as false for past birth bonding leave when claim is pre-populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason(past)
        .create();
      setup(claim);

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_birth_date: past,
            has_future_child_date: false,
          },
        });
      });
    });

    it("sets has_future_child_date as false for past birth bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.newBorn;

      setup(claim);
      const [year, month, day] = past.split("-");
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Month",
        }),
        month
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Day",
        }),
        day
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Year",
        }),
        year
      );
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_birth_date: past,
            has_future_child_date: false,
          },
        });
      });
    });

    it("sets has_future_child_date as false for past placement bonding leave when claim is pre-populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingFosterCareLeaveReason(past)
        .create();
      setup(claim);
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_placement_date: past,
            has_future_child_date: false,
          },
        });
      });
    });

    it("sets has_future_child_date as false for past placement bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.fosterCare;

      setup(claim);
      const [year, month, day] = past.split("-");
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Month",
        }),
        month
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Day",
        }),
        day
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Year",
        }),
        year
      );
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_placement_date: past,
            has_future_child_date: false,
          },
        });
      });
    });
  });
});

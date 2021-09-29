import {
  DurationBasis,
  FrequencyIntervalBasis,
} from "../../../src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import IntermittentFrequency from "../../../src/pages/applications/intermittent-frequency";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const render = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder()
      .intermittent()
      .medicalLeaveReason()
      .create();
  }
  const cb = (appLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };
  return renderPage(
    IntermittentFrequency,
    {
      addCustomSetup: (appLogic) =>
        setupBenefitsApplications(appLogic, [claim], cb),
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("IntermittentFrequency", () => {
  it("renders the page", () => {
    const { container } = render();
    expect(container).toMatchSnapshot();
  });

  it("it displays frequency and duration_basis questions when a frequency_interval_basis is selected", () => {
    render(
      new MockBenefitsApplicationBuilder()
        .intermittent({
          frequency_interval_basis: FrequencyIntervalBasis.months,
        })
        .create()
    );
    expect(
      screen.getByText(/Estimate how many absences over the next 6 months./)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/How long will an absence typically last?/)
    ).toBeInTheDocument();
  });

  it("it displays duration question when a duration_basis is selected", () => {
    render(
      new MockBenefitsApplicationBuilder()
        .intermittent({
          duration_basis: DurationBasis.days,
        })
        .create()
    );

    expect(
      screen.getByText(/How many days of work will you miss per absence?/)
    ).toBeInTheDocument();
    expect(screen.getByText(/At least one day/)).toBeInTheDocument();
  });

  it.each([
    [
      {
        frequency_interval: 3,
        frequency_interval_basis: FrequencyIntervalBasis.weeks,
      },
      "Estimate how many absences per week.",
    ],
    [
      {
        frequency_interval: 3,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
      "Estimate how many absences per month.",
    ],
    [
      {
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
      "Estimate how many absences over the next 6 months.",
    ],
  ])(
    "displays frequency label corresponding to selected frequency interval and basis",
    (frequencyInterval, textToDisplay) => {
      render(
        new MockBenefitsApplicationBuilder()
          .intermittent(frequencyInterval)
          .create()
      );
      expect(screen.getByText(textToDisplay)).toBeInTheDocument();
    }
  );

  it.each([
    [
      {
        duration_basis: DurationBasis.days,
      },
      "At least one day",
    ],
    [
      {
        duration_basis: DurationBasis.hours,
      },
      "Less than one full work day",
    ],
  ])(
    "displays duration label corresponding to selected duration basis",
    (durationBasis, textToDisplay) => {
      render(
        new MockBenefitsApplicationBuilder()
          .intermittent(durationBasis)
          .create()
      );
      expect(screen.getByText(textToDisplay)).toBeInTheDocument();
    }
  );

  it("displays Alert about having form + Lead when claim is caring leave", () => {
    render(
      new MockBenefitsApplicationBuilder()
        .caringLeaveReason()
        .intermittent()
        .create()
    );
    expect(
      screen.getByRole("heading", { name: "Leave details" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "Certification of Your Family Member’s Serious Health Condition",
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Your answers must match the intermittent leave section in the Certification of Your Family Member’s Serious Health Condition./
      )
    ).toBeInTheDocument();
  });

  it("displays Alert about having form + Lead when claim is medical leave", () => {
    render(
      new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .intermittent()
        .create()
    );
    expect(
      screen.getByRole("heading", { name: "Leave details" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Certification of Your Serious Health Condition",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Your answers must match the intermittent leave section in the Certification of Your Serious Health Condition./
      )
    ).toBeInTheDocument();
  });

  it("enables user to change frequency of their leave", async () => {
    render();
    userEvent.click(
      screen.getByRole("radio", { name: "Once or more per week" })
    );
    await waitFor(() => {
      expect(
        screen.getByRole("radio", { name: "Once or more per week" })
      ).toBeChecked();
    });
  });

  it("enables user to select irregular over 6 months radio", async () => {
    render();
    userEvent.click(
      screen.getByRole("radio", { name: "Irregular over the next 6 months" })
    );
    await waitFor(() => {
      expect(
        screen.getByRole("radio", { name: "Irregular over the next 6 months" })
      ).toBeChecked();
    });
  });

  it("sends the page's fields and the leave period ID to the API when the data is already on the claim", async () => {
    const claim = new MockBenefitsApplicationBuilder().intermittent().create();
    const {
      duration,
      duration_basis,
      frequency,
      frequency_interval,
      frequency_interval_basis,
      leave_period_id,
    } = claim.leave_details.intermittent_leave_periods[0];

    render(claim);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          intermittent_leave_periods: [
            {
              duration,
              duration_basis,
              frequency,
              frequency_interval,
              frequency_interval_basis,
              leave_period_id,
            },
          ],
        },
      });
    });
  });

  it("sends the page's fields and the leave period ID to the API when the data is newly entered", async () => {
    const claim = new MockBenefitsApplicationBuilder().intermittent().create();

    const frequency_interval_basis = FrequencyIntervalBasis.months;
    const frequency = 6;
    const frequency_interval = 6;
    const duration_basis = DurationBasis.hours;
    const duration = 6;

    render(claim);

    userEvent.click(
      screen.getByRole("radio", { name: "Irregular over the next 6 months" })
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Estimate how many absences over the next 6 months.",
      }),
      "{backspace}6"
    );
    userEvent.click(
      screen.getByRole("radio", { name: "Less than one full work day" })
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "How many hours of work will you miss per absence?",
      }),
      "{backspace}6"
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          intermittent_leave_periods: [
            {
              duration,
              duration_basis,
              frequency,
              frequency_interval,
              frequency_interval_basis,
              leave_period_id: "mock-leave-period-id",
            },
          ],
        },
      });
    });
  });
});

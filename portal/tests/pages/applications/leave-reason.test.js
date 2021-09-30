import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import LeaveReason from "../../../src/models/LeaveReason";
import LeaveReasonPage from "../../../src/pages/applications/leave-reason";
import { ReasonQualifier } from "../../../src/models/BenefitsApplication";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

function setup(
  { claim } = { claim: new MockBenefitsApplicationBuilder().create() }
) {
  const updateSpy = jest.fn();

  const utils = renderPage(
    LeaveReasonPage,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateSpy;
      },
    },
    {
      query: { claim_id: claim.application_id },
    }
  );

  return {
    updateSpy,
    ...utils,
  };
}

describe("LeaveReason", () => {
  it("renders the page without the military leave option", () => {
    const { container } = setup();

    expect(container).toMatchSnapshot();
  });

  it("renders military leave options when feature flag is enabled", () => {
    process.env.featureFlags = {
      claimantShowMilitaryLeaveTypes: true,
    };

    setup();

    expect(
      screen.getAllByRole("radio", {
        name: /armed forces/i,
      })
    ).toHaveLength(2);
  });

  it("selects Medical leave reason if the reason on the existing claim is Pregnancy", () => {
    setup({
      claim: new MockBenefitsApplicationBuilder()
        .pregnancyLeaveReason()
        .create(),
    });

    expect(
      screen.getByRole("radio", { name: /illness, injury/i })
    ).toBeChecked();
  });

  it.each([
    ["Medical", LeaveReason.medical, /illness, injury/i],
    ["Caring", LeaveReason.care, /care for my family member/i],
    [
      "Military",
      LeaveReason.activeDutyFamily,
      /manage family affairs while a family member is on active duty/i,
    ],
    [
      "Military Caring",
      LeaveReason.serviceMemberFamily,
      /care for a family member who serves in the armed forces/i,
    ],
  ])(
    "clears bonding leave fields and submits leave reason when user selects %s leave option",
    async (_testLabel, reason, radioName) => {
      process.env.featureFlags = {
        claimantShowMilitaryLeaveTypes: true,
      };
      const { updateSpy } = setup();

      userEvent.click(screen.getByRole("radio", { name: radioName }));
      userEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() =>
        expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
          leave_details: {
            child_birth_date: null,
            child_placement_date: null,
            pregnant_or_recent_birth: null,
            has_future_child_date: null,
            reason_qualifier: null,
            reason,
          },
        })
      );
    }
  );

  it("submits leave reason AND reason qualifier when user selects Bonding leave options", async () => {
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("radio", { name: /bond with my child/i }));
    userEvent.click(screen.getByRole("radio", { name: "Adoption" }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          pregnant_or_recent_birth: null,
          reason: LeaveReason.bonding,
          reason_qualifier: ReasonQualifier.adoption,
        },
      })
    );
  });

  it("instructs the user to review their previous leaves when user changes their leave reason after reporting previous leaves for the same reason", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .caringLeaveReason()
      .previousLeavesSameReason()
      .create();

    const alertTextMatch = /review your previous leave/i;

    setup({ claim });

    // Haven't changed our answer yet, so shouldn't be visible
    expect(
      screen.queryByRole("heading", { name: alertTextMatch })
    ).not.toBeInTheDocument();

    userEvent.click(screen.getByRole("radio", { name: /bond with my child/i }));

    expect(
      screen.getByRole("heading", { name: alertTextMatch }).parentNode
    ).toMatchSnapshot();
  });

  it("does not instruct the user to review their previous leaves when user changes their leave reason but didn't have previous leaves for the same reason", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .caringLeaveReason()
      .previousLeavesSameReason([])
      .create();
    setup({ claim });

    userEvent.click(screen.getByRole("radio", { name: /bond with my child/i }));

    expect(
      screen.queryByRole("heading", { name: /review your previous leave/i })
    ).not.toBeInTheDocument();
  });
});

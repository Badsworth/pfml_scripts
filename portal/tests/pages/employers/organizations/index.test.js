import User, { UserLeaveAdministrator } from "../../../../src/models/User";
import { cleanup, screen } from "@testing-library/react";
import Index from "../../../../src/pages/employers/organizations";
import { renderPage } from "../../../test-utils";
import routeWithParams from "../../../../src/utils/routeWithParams";

const verifiedAdministrator = new UserLeaveAdministrator({
  employer_dba: "Knitting Castle",
  employer_fein: "11-3453443",
  employer_id: "dda930f-93jfk-iej08",
  has_fineos_registration: true,
  has_verification_data: true,
  verified: true,
});

const verifiableAdministrator = new UserLeaveAdministrator({
  employer_dba: "Book Bindings 'R Us",
  employer_fein: "00-3451823",
  employer_id: "dda903f-f093f-ff900",
  has_fineos_registration: true,
  has_verification_data: true,
  verified: false,
});

const unverifiableAdministrator = new UserLeaveAdministrator({
  employer_dba: "Tomato Touchdown",
  employer_fein: "22-3457192",
  employer_id: "io19fj9-00jjf-uiw3r",
  has_fineos_registration: true,
  has_verification_data: false,
  verified: false,
});

const EMPLOYERS = [
  verifiableAdministrator,
  verifiedAdministrator,
  unverifiableAdministrator,
];

const setup = (employers = [], props = {}) => {
  return renderPage(
    Index,
    {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          consented_to_data_sharing: true,
          user_leave_administrators: employers,
        });
      },
    },
    { query: { account_converted: "false" }, ...props }
  );
};

describe("Index", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("show the correct empty state", () => {
    setup();
    expect(
      screen.getByRole("row", { name: "None reported" })
    ).toBeInTheDocument();
  });

  it("displays a table row for each user leave administrator", () => {
    setup(EMPLOYERS);
    expect(
      screen.queryByRole("row", { name: "None reported" })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("row", {
        name: "Book Bindings 'R Us Verification required 00-3451823",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("row", { name: "Knitting Castle 11-3453443" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("row", {
        name: "Tomato Touchdown Verification blocked 22-3457192",
      })
    ).toBeInTheDocument();
  });

  it("displays a button linked to Add Organization page", () => {
    setup();
    expect(
      screen.getByRole("link", { name: "Add organization" })
    ).toBeInTheDocument();
  });

  it("shows an Alert telling the user to start verification if there are unverified employers", () => {
    const verifyAccountDescription =
      /Every employer must verify paid leave contributions when creating an account./;
    setup(EMPLOYERS);
    expect(
      screen.queryByRole("heading", {
        name: "Verify your account",
      })
    ).toBeInTheDocument();

    expect(screen.queryByText(verifyAccountDescription)).toBeInTheDocument();
    expect(screen.getByRole("region")).toMatchSnapshot();

    cleanup();
    setup([verifiedAdministrator]);
    expect(
      screen.queryByRole("heading", {
        name: "Verify your account",
      })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(verifyAccountDescription)
    ).not.toBeInTheDocument();
  });

  it("shows the 'Verification required' tag and link for verifiable administrators", () => {
    setup([verifiableAdministrator]);
    expect(
      screen.getByRole("rowheader", {
        name: "Book Bindings 'R Us Verification required",
      })
    ).toMatchSnapshot();
  });

  it("shows the 'Verification blocked' tag and link for unverifiable administrators", () => {
    setup([unverifiableAdministrator]);
    expect(
      screen.getByRole("rowheader", {
        name: "Tomato Touchdown Verification blocked",
      })
    ).toMatchSnapshot();
  });

  it("links to the cannot verify page for unverifiable administrators", () => {
    setup([unverifiableAdministrator]);
    const expectedUrl = routeWithParams("employers.cannotVerify", {
      employer_id: unverifiableAdministrator.employer_id,
    });
    expect(
      screen.getByRole("link", { name: unverifiableAdministrator.employer_dba })
    ).toHaveAttribute("href", expectedUrl);
  });

  it("does not show the 'Verification required' tag for verified administrators", () => {
    setup([verifiedAdministrator]);
    expect(
      screen.queryByRole("link", { name: "Verification required" })
    ).not.toBeInTheDocument();
  });

  it("does not render links for verified administrators", () => {
    setup([verifiedAdministrator]);
    expect(
      screen.queryByRole("link", { name: verifiedAdministrator.employer_dba })
    ).not.toBeInTheDocument();
  });

  it("shows a success message telling the user they are now a leave admin", () => {
    setup([], { query: { account_converted: "true" } });
    expect(
      screen.getByRole("heading", { name: "Success" })
    ).toBeInTheDocument();
    expect(screen.getByRole("region")).toMatchSnapshot();
  });
});

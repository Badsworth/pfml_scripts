import { screen, waitFor } from "@testing-library/react";
import { Start } from "../../../src/pages/applications/start";
import { renderPage } from "../../test-utils";
import userEvent from "@testing-library/user-event";

describe("Start", () => {
  it("renders the page", () => {
    const { container } = renderPage(Start);
    expect(container).toMatchSnapshot();
  });

  it("renders descriptions with mass gov link", () => {
    renderPage(Start);
    expect(
      screen.getByRole("heading", { name: "Start your application" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /We use this application to determine the leave time and benefit amount you will receive./
      )
    ).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      "https://www.mass.gov/info-details/massachusetts-department-of-family-and-medical-leave-informed-consent-agreement"
    );
  });

  it("creates application when user clicks agree and submit", async () => {
    const create = jest.fn();
    renderPage(Start, {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.create = create;
      },
    });
    userEvent.click(
      screen.getByRole("button", { name: "I understand and agree" })
    );
    await waitFor(() => {
      expect(create).toHaveBeenCalled();
    });
  });
});

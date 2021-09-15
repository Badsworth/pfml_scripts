import User, { RoleDescription, UserRole } from "../../src/models/User";

import Header from "../../src/components/Header";
import React from "react";
import { render } from "@testing-library/react";
import { within } from "@testing-library/dom";

describe("Header", () => {
  describe("Header navigation links", () => {
    it("includes a Skip Nav link with correct class and href", () => {
      const header = render(<Header onLogout={jest.fn()} />);
      const skipNavLink = header.getByRole("link", {
        name: /skip to main content/i,
      });

      expect(skipNavLink).toHaveAttribute("href", "#main");
      expect(skipNavLink).toHaveClass("usa-skipnav");
      expect(skipNavLink).toMatchSnapshot();
    });

    it("includes a Back to Mass.gov link with correct class and href", () => {
      const header = render(<Header onLogout={jest.fn()} />);
      const backToMassLink = header.getByRole("link", {
        name: /back to mass\.gov/i,
      });

      expect(backToMassLink).toHaveAttribute(
        "href",
        "https://www.mass.gov/topics/paid-family-and-medical-leave-in-massachusetts"
      );
      expect(backToMassLink).toHaveClass("usa-button");
      expect(backToMassLink).toMatchSnapshot();
    });
  });

  describe("Header log-in behavior", () => {
    it("renders header with user's information for a logged-in claimant", () => {
      const user = new User({
        email_address: "email@address.com",
        user_id: "mock-user-id",
      });

      const header = render(<Header onLogout={jest.fn()} user={user} />);
      const betaSection = header.queryByText(/beta/i);
      const emailSection = header.getByTestId("email_address");
      const userEmailAddress = within(emailSection).getByText(
        user.email_address
      );

      expect(betaSection).toBeInTheDocument();
      expect(betaSection).toMatchSnapshot();
      expect(userEmailAddress).toBeInTheDocument();
      expect(userEmailAddress).toMatchSnapshot();
    });

    it("doesn't render beta banner when user isn't logged in", () => {
      const header = render(<Header onLogout={jest.fn()} />);
      const betaSection = header.queryByText(/beta/i);
      expect(betaSection).not.toBeInTheDocument();
    });

    it("renders employer feedback link when user is an employer", () => {
      const user = new User({
        email_address: "email@address.com",
        user_id: "mock-user-id",
        roles: [
          new UserRole({
            role_description: RoleDescription.employer,
          }),
        ],
      });

      const header = render(<Header onLogout={jest.fn()} user={user} />);
      const feedbackLink = header.getByText(/your feedback/);

      expect(feedbackLink).toHaveAttribute(
        "href",
        "https://www.mass.gov/paidleave-employer-feedback"
      );
      expect(feedbackLink).toMatchSnapshot();
    });
  });

  describe("Header maintenance alert bar", () => {
    const maintenanceText = /maintenance on our system/;
    const maintenanceStartTime = "10:15 PM (EST)";
    const maintenanceEndTime = "12:45 AM (EST)";

    it("renders maintenance alert bar when maintenance is enabled", () => {
      const header = render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceEndTime={maintenanceEndTime}
          maintenanceStartTime={maintenanceStartTime}
        />
      );

      const alert = header.queryByText(maintenanceText);
      const startTimeText = header.getByText(maintenanceStartTime);
      const endTimeText = header.getByText(maintenanceEndTime);

      expect(alert).toBeInTheDocument();
      expect(startTimeText).toBeInTheDocument();
      expect(endTimeText).toBeInTheDocument();
      expect(alert).toMatchSnapshot();
      expect(startTimeText).toMatchSnapshot();
      expect(endTimeText).toMatchSnapshot();
    });

    it("renders maintenance alert bar when only start time is provided", () => {
      const header = render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceStartTime={maintenanceStartTime}
        />
      );

      const alert = header.queryByText(maintenanceText);
      const startTimeText = header.getByText(maintenanceStartTime);

      expect(alert).toBeInTheDocument();
      expect(startTimeText).toBeInTheDocument();
      expect(alert).toMatchSnapshot();
      expect(startTimeText).toMatchSnapshot();
    });

    it("doesn't render maintenance alert bar when maintenance is disabled", () => {
      const header = render(<Header onLogout={jest.fn()} />);
      const alert = header.queryByText(maintenanceText);
      expect(alert).not.toBeInTheDocument();
    });

    it("doesn't render maintenance alert bar when only end time is provided", () => {
      const header = render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceEndTime={maintenanceEndTime}
        />
      );
      const alert = header.queryByText(maintenanceText);
      expect(alert).not.toBeInTheDocument();
    });
  });
});

import User, { RoleDescription, UserRole } from "../../src/models/User";
import { render, screen, within } from "@testing-library/react";
import Header from "../../src/components/Header";
import React from "react";

describe("Header", () => {
  describe("Header navigation links", () => {
    it("includes a Skip Nav link with correct class and href", () => {
      render(<Header onLogout={jest.fn()} />);
      const skipNavLink = screen.getByRole("link", {
        name: /skip to main content/i,
      });

      expect(skipNavLink).toHaveAttribute("href", "#main");
      expect(skipNavLink).toHaveClass("usa-skipnav");
      expect(skipNavLink).toMatchSnapshot();
    });

    it("includes a Back to Mass.gov link with correct class and href", () => {
      render(<Header onLogout={jest.fn()} />);
      const backToMassLink = screen.getByRole("link", {
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

      render(<Header onLogout={jest.fn()} user={user} />);
      const betaSection = screen.queryByText(/beta/i);
      const emailSection = screen.getByTestId("email_address");
      const userEmailAddress = within(emailSection).getByText(
        user.email_address
      );

      expect(betaSection).toBeInTheDocument();
      expect(betaSection).toMatchSnapshot();
      expect(userEmailAddress).toBeInTheDocument();
      expect(userEmailAddress).toMatchSnapshot();
    });

    it("doesn't render beta banner when user isn't logged in", () => {
      render(<Header onLogout={jest.fn()} />);
      const betaSection = screen.queryByText(/beta/i);
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

      render(<Header onLogout={jest.fn()} user={user} />);
      const feedbackLink = screen.getByText(/your feedback/);

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
      render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceEndTime={maintenanceEndTime}
          maintenanceStartTime={maintenanceStartTime}
        />
      );

      const alert = screen.queryByText(maintenanceText);
      const startTimeText = screen.getByText(maintenanceStartTime);
      const endTimeText = screen.getByText(maintenanceEndTime);

      expect(alert).toBeInTheDocument();
      expect(startTimeText).toBeInTheDocument();
      expect(endTimeText).toBeInTheDocument();
      expect(alert).toMatchSnapshot();
      expect(startTimeText).toMatchSnapshot();
      expect(endTimeText).toMatchSnapshot();
    });

    it("renders maintenance alert bar when only start time is provided", () => {
      render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceStartTime={maintenanceStartTime}
        />
      );

      const alert = screen.queryByText(maintenanceText);
      const startTimeText = screen.getByText(maintenanceStartTime);

      expect(alert).toBeInTheDocument();
      expect(startTimeText).toBeInTheDocument();
      expect(alert).toMatchSnapshot();
      expect(startTimeText).toMatchSnapshot();
    });

    it("doesn't render maintenance alert bar when maintenance is disabled", () => {
      render(<Header onLogout={jest.fn()} />);
      const alert = screen.queryByText(maintenanceText);
      expect(alert).not.toBeInTheDocument();
    });

    it("doesn't render maintenance alert bar when only end time is provided", () => {
      render(
        <Header
          onLogout={jest.fn()}
          showUpcomingMaintenanceAlertBar
          maintenanceEndTime={maintenanceEndTime}
        />
      );
      const alert = screen.queryByText(maintenanceText);
      expect(alert).not.toBeInTheDocument();
    });
  });
});

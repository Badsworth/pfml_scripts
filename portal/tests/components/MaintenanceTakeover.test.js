import MaintenanceTakeover from "../../src/components/MaintenanceTakeover";
import React from "react";
import { render } from "@testing-library/react";

describe("MaintenanceTakeover", () => {
  it("renders the correct message text when start/end times are both provided", () => {
    const { container } = render(
      <MaintenanceTakeover
        maintenanceStartTime="June 15, 2021, 3:00 PM EDT"
        maintenanceEndTime="June 17, 2021, 10:00 AM EDT"
      />
    );

    expect(container).toMatchSnapshot();
  });

  it("renders the correct message text when only end time is provided", () => {
    const { container } = render(
      <MaintenanceTakeover
        maintenanceStartTime={null}
        maintenanceEndTime="June 17, 2021, 10:00 AM EDT"
      />
    );

    expect(container).toMatchSnapshot();
  });

  it("renders the correct message text when start/end times are not provided", () => {
    const { container } = render(
      <MaintenanceTakeover
        maintenanceStartTime={null}
        maintenanceEndTime={null}
      />
    );

    expect(container).toMatchSnapshot();
  });
});

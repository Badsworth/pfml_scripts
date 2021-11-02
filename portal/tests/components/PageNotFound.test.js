import { render, waitFor } from "@testing-library/react";
import PageNotFound from "../../src/components/PageNotFound";
import React from "react";
import tracker from "../../src/services/tracker";

jest.mock("../../src/services/tracker");

describe("PageNotFound", () => {
  it("renders with expected content and links", () => {
    const { container } = render(<PageNotFound />);
    expect(container).toMatchSnapshot();
  });

  it("tracks an event", async () => {
    render(<PageNotFound />);

    await waitFor(() => {
      expect(tracker.trackEvent).toHaveBeenCalledTimes(1);
      expect(tracker.trackEvent).toHaveBeenCalledWith("Page not found");
    });
  });
});

import { ManagedRequirement } from "../../src/models/Claim";
import getClosestOpenFollowUpDate from "../../src/utils/getClosestOpenFollowUpDate";

const setManagedRequirement = (
  customProps?: Partial<ManagedRequirement>
): ManagedRequirement => ({
  category: "",
  created_at: "",
  follow_up_date: "2021-08-22",
  responded_at: "",
  status: "Open",
  type: "",
  ...customProps,
});

describe("getClosestOpenFollowUpDate", () => {
  it("return the formatted follow up date", () => {
    expect(getClosestOpenFollowUpDate([setManagedRequirement()])).toBe(
      "8/22/2021"
    );
  });
  it("returns undefined if there is no managed requirement", () => {
    expect(getClosestOpenFollowUpDate([])).toBe(undefined);
  });

  it("returns undefined if there is no open managed requirement", () => {
    expect(
      getClosestOpenFollowUpDate([
        setManagedRequirement({ status: "Complete" }),
      ])
    ).toBe(undefined);
  });

  it("returns the closest follow update if there are multiple open managed requirement", () => {
    expect(
      getClosestOpenFollowUpDate([
        setManagedRequirement(),
        setManagedRequirement({ follow_up_date: "2021-09-22" }),
        setManagedRequirement({ follow_up_date: "2021-07-22" }),
      ])
    ).toBe("7/22/2021");
  });
});

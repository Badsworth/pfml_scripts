import { ManagedRequirement } from "../../src/models/ManagedRequirement";

export const createMockManagedRequirement = (
  customAttrs: Partial<ManagedRequirement> = {}
): ManagedRequirement => ({
  created_at: "2020-01-01T00:00:00.000Z",
  follow_up_date: null,
  responded_at: null,
  status: "Open",
  category: "Employer Confirmation",
  type: "Employer Confirmation of Leave Data",
  ...customAttrs,
});

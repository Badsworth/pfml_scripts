/**
 * @file Mock Feature Flag API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/FeatureFlagApi")
 */

import Flag from "../../models/Flag";

export const getFlagsMock = jest.fn().mockResolvedValue(() => {
  return [
    new Flag({
      name: "maintenance",
      enabled: true,
      start: null,
      end: null,
      options: {
        page_routes: ["/*"],
      },
    }),
  ];
});

export default jest.fn().mockImplementation(() => ({
  getFlags: getFlagsMock,
}));

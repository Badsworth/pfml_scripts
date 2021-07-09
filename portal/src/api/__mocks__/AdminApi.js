/**
 * @file Mock Admin API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/AdminApi")
 */

import Flag from "../../models/Flag";

export const getFlagsMock = jest.fn().mockResolvedValue(() => {
  return {
    data: [
      new Flag({
        name: "maintenance",
        enabled: true,
        start: null,
        end: null,
        options: {
          page_routes: ["/*"],
        },
      }),
    ],
    status: 200,
    success: true,
  };
});

export default jest.fn().mockImplementation(() => ({
  getFlags: getFlagsMock,
}));

import { NetworkError } from "../src/errors";

describe("errors", () => {
  describe("NetworkError", () => {
    it("creates a NetworkError", () => {
      const error = new NetworkError("Network failure");

      expect(error).toMatchInlineSnapshot(`[NetworkError: Network failure]`);
    });
  });
});

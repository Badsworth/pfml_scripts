import { testHook } from "../test-utils";
import useUniqueId from "../../src/hooks/useUniqueId";

describe("useUniqueId", () => {
  it("generates unique id with given prefix", () => {
    let uniqueIdA, uniqueIdB;

    testHook(() => {
      uniqueIdA = useUniqueId("field");
      uniqueIdB = useUniqueId("field");
    });

    expect(uniqueIdA).toMatch(/field\d/);
    expect(uniqueIdB).toMatch(/field\d/);
    expect(uniqueIdA).not.toEqual(uniqueIdB);
  });
});

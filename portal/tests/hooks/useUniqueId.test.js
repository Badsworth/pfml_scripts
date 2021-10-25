import { renderHook } from "@testing-library/react-hooks";
import useUniqueId from "../../src/hooks/useUniqueId";

describe("useUniqueId", () => {
  it("generates unique id with given prefix", () => {
    let uniqueIdA, uniqueIdB;

    renderHook(() => {
      uniqueIdA = useUniqueId("field");
      uniqueIdB = useUniqueId("field");
    });

    expect(uniqueIdA).toMatch(/field\d/);
    expect(uniqueIdB).toMatch(/field\d/);
    expect(uniqueIdA).not.toEqual(uniqueIdB);
  });
});

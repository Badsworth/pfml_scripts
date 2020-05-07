import AppErrorInfo from "../../src/models/AppErrorInfo";

describe("AppErrorInfo", () => {
  it("generates a unique key for each instance", () => {
    const errorInfo1 = new AppErrorInfo({ message: "One" });
    const errorInfo2 = new AppErrorInfo({ message: "Two" });

    expect(errorInfo1.key).toEqual(expect.stringContaining("AppErrorInfo"));
    expect(errorInfo2.key).toEqual(expect.stringContaining("AppErrorInfo"));
    expect(errorInfo1.key).not.toEqual(errorInfo2.key);
  });
});

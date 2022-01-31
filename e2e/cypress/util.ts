export const describeIf = (
  condition: boolean,
  label: string,
  opts: Mocha.MochaOptions,
  suiteFn: Parameters<Mocha.SuiteFunction>[2]
): void => {
  (condition ? describe : describe.skip)(label, opts, suiteFn);
};

export const itIf = (
  condition: boolean,
  label: string,
  opts: Mocha.MochaOptions,
  testFn: Mocha.Func | Mocha.AsyncFunc
): void => {
  (condition ? it : it.skip)(label, opts, testFn);
};

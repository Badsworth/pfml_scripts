import { config } from "./actions/common";

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

export const getTwilioNumber = (index: number): string => {
  const numbers = config("TWILIO_NUMBERS").split(",");
  if (typeof numbers[index] !== "string" || numbers[index].length < 1) {
    throw new Error(
      `TWILIO_NUMBERS does not include an element for index ${index}.`
    );
  }
  return numbers[index];
};

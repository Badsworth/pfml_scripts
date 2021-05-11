import { initializeI18n } from "../../src/locales/i18n";

const NON_BREAKING_HYPHEN = "‑";

describe("i18n formatters", () => {
  it("formats currency values", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          dollarAmount: "{{amount, currency}}",
        },
      },
    });

    expect(t("dollarAmount", { amount: 1000 })).toBe("$1,000.00");
  });

  it("formats employer FEINs", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          ein: "{{employer_fein, ein}}",
        },
      },
    });

    const expected = "12" + NON_BREAKING_HYPHEN + "3456789";
    expect(t("ein", { employer_fein: "12-3456789" })).toBe(expected);
  });

  it("formats hour and minute durations", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          hoursMinutesDuration: "{{minutes, hoursMinutesDuration}}",
        },
      },
    });

    expect(t("hoursMinutesDuration", { minutes: 475 })).toBe("7h 55m");
    expect(t("hoursMinutesDuration", { minutes: 45 })).toBe("0h 45m");
    expect(t("hoursMinutesDuration", { minutes: 0 })).toBe("0h");
  });
});

import { initializeI18n } from "../../src/locales/i18n";
import tracker from "../../src/services/tracker";

describe("i18n", () => {
  it("returns initial value when the format is unexpected", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          unknownFormat: "{{amount, foo}}",
        },
      },
    });

    expect(t("unknownFormat", { amount: 1000 })).toBe("1000");
  });

  it("tracks missing keys", async () => {
    const spy = jest.spyOn(tracker, "trackEvent");
    const t = await initializeI18n();

    t("this.key.doesnt.exist");

    expect(spy).toHaveBeenCalledWith("Missing i18n key", {
      i18nContext: "",
      i18nKey: "this.key.doesnt.exist",
      i18nLocales: '["en-US"]',
      i18nNamespace: "translation",
    });
  });

  it("tracks missing key context", async () => {
    const spy = jest.spyOn(tracker, "trackEvent");
    const t = await initializeI18n();

    t("testKey", { context: "pregnant" });

    expect(spy).toHaveBeenCalledWith("Missing i18n key", {
      i18nContext: "pregnant",
      i18nKey: "testKey",
      i18nLocales: '["en-US"]',
      i18nNamespace: "translation",
    });
  });

  it("returns the original key when the key is missing", async () => {
    const t = await initializeI18n();

    const content = t("this.key.doesnt.exist");

    expect(content).toBe("this.key.doesnt.exist");
  });

  it("tracks missing interpolation values", async () => {
    const spy = jest.spyOn(tracker, "trackEvent");
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          testKey: "I like {{ fruitA }}, {{ fruitB }}, and {{ fruitC }}.",
        },
      },
    });

    const content = t("testKey", { fruitB: "banana" });

    expect(spy).toHaveBeenNthCalledWith(1, "Missing i18n interpolation value", {
      i18nValueMissing: "{{ fruitA }},  fruitA ",
      i18nTextStartsWith: "I like {{ fruitA }}, {{ fruitB }}, and {", // truncated
    });
    expect(spy).toHaveBeenNthCalledWith(2, "Missing i18n interpolation value", {
      i18nValueMissing: "{{ fruitC }},  fruitC ",
      i18nTextStartsWith: "I like , banana, and {{ fruitC }}.",
    });
    expect(content).toBe("I like , banana, and .");
  });

  it("exposes fileSizeMaxMB as a global interpolation value, based on the fileSizeMaxBytesFineos env var", async () => {
    process.env.fileSizeMaxBytesFineos = "1000000";

    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          testKey: "{{ fileSizeMaxMB }} MB",
        },
      },
    });

    const content = t("testKey");

    expect(content).toBe("1 MB");
  });
});

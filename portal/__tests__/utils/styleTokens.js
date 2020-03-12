import styleTokens from "../../src/utils/styleTokens";

// These are somewhat odd test cases since this method is dependent
// on CSS existing on an HTML element. We need to mock some methods
// like getComputedStyle to support that in Jest...
describe("styleTokens", () => {
  afterEach(() => {
    document.defaultView.getComputedStyle = jest.fn();
  });

  it("returns JSON stored on the `html` element's `content` CSS property", () => {
    const mockContent =
      '{ "color-primary": "#ff0000", "color-secondary": "blue" }';

    document.defaultView.getComputedStyle = jest.fn(() => ({
      getPropertyValue: () => mockContent,
    }));

    expect(styleTokens()).toMatchInlineSnapshot(`
      Object {
        "color-primary": "#ff0000",
        "color-secondary": "blue",
      }
    `);
  });

  describe("when html:after doesn't have a value for `content`", () => {
    it("returns empty object", () => {
      const mockContent = null;

      document.defaultView.getComputedStyle = jest.fn(() => ({
        getPropertyValue: () => mockContent,
      }));

      expect(styleTokens()).toEqual({});
    });
  });

  describe("when html:after has a value for `content` that contains invalid JSON", () => {
    beforeAll(() => {
      // Don't show a scary error in our log when it's expected
      jest.spyOn(console, "error").mockImplementation(() => null);
    });

    afterAll(() => {
      console.error.mockRestore();
    });

    it("returns empty object", () => {
      const mockContent = "This isn't JSON!";

      document.defaultView.getComputedStyle = jest.fn(() => ({
        getPropertyValue: () => mockContent,
      }));

      expect(styleTokens()).toEqual({});
    });
  });
});

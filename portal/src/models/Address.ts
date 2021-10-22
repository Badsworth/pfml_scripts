class Address {
  city: string | null = null;
  line_1: string | null = null;
  line_2: string | null = null;
  state: string | null = null;
  zip: string | null = null;

  constructor(attrs: Partial<Address>) {
    Object.assign(this, attrs);
  }

  get toString(): string {
    return `${this.line_1 || ""} ${this.line_2 || ""}, ${this.city || ""}, ${
      this.state || ""
    } ${this.zip || ""}`
      .replace("  ", " ")
      .replace(", ,", "")
      .trim();
  }
}

export default Address;

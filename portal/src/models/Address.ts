class Address {
  city: string | null = null;
  line_1: string | null = null;
  line_2: string | null = null;
  state: string | null = null;
  zip: string | null = null;

  constructor(attrs: Partial<Address>) {
    Object.assign(this, attrs);
  }

  toString(): string {
    return (
      `${this.line_1 || ""} ${this.line_2 || ""}, ${this.city || ""} ${
        this.state || ""
      } ${this.zip || ""}`
        // remove double spaces
        .replace("  ", " ")
        .trim()
        // clear space after line 1
        .replace(" ,", ",")
        // remove trailing comma
        .replace(/(.), ?$/, "$1")
        // remove starting comma
        .replace(/^ ?, ?(.)/, "$1")
    );
  }
}

export default Address;

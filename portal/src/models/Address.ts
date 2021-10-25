class Address {
  city: string | null = null;
  line_1: string | null = null;
  line_2: string | null = null;
  state: string | null = null;
  zip: string | null = null;

  constructor(attrs: Partial<Address>) {
    Object.assign(this, attrs);
  }
}

export default Address;

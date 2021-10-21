class Withholding {
  filing_period: string | null = null;

  constructor(attrs: Withholding) {
    Object.assign(this, attrs);
  }
}

export default Withholding;

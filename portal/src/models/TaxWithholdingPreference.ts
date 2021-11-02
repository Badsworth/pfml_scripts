class TaxWithholdingPreference {
  withhold_taxes: boolean;

  constructor(attrs: TaxWithholdingPreference) {
    Object.assign(this, attrs);
  }
}

export default TaxWithholdingPreference;

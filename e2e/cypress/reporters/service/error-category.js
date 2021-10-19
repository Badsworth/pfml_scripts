class ErrorCategory {
  constructor() {
    this.CATEGORY = {
      CONTENT: "content",
      INFRASTRUCTURE_CONNECTION: "infrastructure",
      KNOWN: "known",
      NOTIFICATION: "notification",
    };

    this.SUB_CATEGORY = {
      CONTENT: {
        EDM: "potential-edm",
        UPDATE: "test-update",
      },
      INFRASTRUCTURE_CONNECTION: {
        TIMEOUT: "timeout-service",
        AUTH: "authentication",
        FAILURE400: "failure-400",
        FAILURE500: "failure-500",
        FAILURE503: "failure-503",
        FAILURE504: "failure-504",
      },
      KNOWN: {
        TMP_FILES: "tmp",
        SYNC_SKIP: "sync",
        EMAIL_SUBJECT: "email-subject",
        DOWNLOADS: "downloads",
      },
      NOTIFICATION: {},
    };

    this.RuleBuilder = new RuleBuilder();
    this.buildRules();
  }

  buildRules() {
    /*ignore jslint start*/
    // prettier-ignore
    this.RuleBuilder
    /**
     * Content issues
     */
        .setCategory(this.CATEGORY.CONTENT)
          .setSubCategory(this.SUB_CATEGORY.CONTENT.EDM)
            .addRule(`AssertionError`, `*Expected to find content*`)
            .addRule(`AssertionError`, `*Expected to find element*`)
            .addRule(`AssertionError`, `*Expected to find a *`)
            .addRule(`AssertionError`, `*expected * to contain text * but the text was*`)
            .addRule(`AssertionError`, `*expected * to have class *`)
            .addRule(`AssertionError`, `*Timed out retrying % expected % to include '/applications/success'%*`)

          .setSubCategory(this.SUB_CATEGORY.CONTENT.UPDATE)
            .addRule(`TestingLibraryElementError`, `*Unable to find*with the text*`)
            .addRule(`TestingLibraryElementError`, `*Found multiple elements with the text*`)
            .addRule(`CypressError`, `*failed because it targeted a disabled element*`)
            .addRule(`CypressError`, `*Timed out*cy.click()*failed because this element*disabled*`)
            .addRule(`CypressError`, `*failed because this element is not visible*`)
            .addRule(`CypressError`, `*failed because this element is detached from the DOM*`)
    /**
     * Infrastructure and Connection issues
     */
        .setCategory(this.CATEGORY.INFRASTRUCTURE_CONNECTION)
          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.TIMEOUT)
            .addRule(`CypressError`, `*cy.task('waitForClaimDocuments')*timed out*`)
            .addRule(`CypressError`, `*cy.visit()*failed trying to load:*fineos.com*`)
            .addRule(`CypressError`, `*Timed out after waiting*`)

          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.AUTH)
            .addRule(`CypressError`, `*cy.task('The application redirected * more than * times*`)

          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.FAILURE400)
            .addRule(`Error`, `*Application submission failed:*(400*`)
            .addRule(`CypressError`, `*cy.task('submitClaimToAPI')*(400*`)

          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.FAILURE500)
            .addRule(`Error`, `*Application submission failed:*(500*`)
            .addRule(`CypressError`, `*cy.task('submitClaimToAPI')*(500*`)

          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.FAILURE503)
            .addRule(`Error`, `*Application submission failed:*(503*`)
            .addRule(`CypressError`, `*cy.task('submitClaimToAPI')*(503*`)

          .setSubCategory(this.SUB_CATEGORY.INFRASTRUCTURE_CONNECTION.FAILURE504)
            .addRule(`Error`, `*Application submission failed:*(504*`)
            .addRule(`CypressError`, `*cy.task('submitClaimToAPI')*(504*`)

    /**
     * Known Issues
     */
        .setCategory(this.CATEGORY.KNOWN)
          .setSubCategory(this.SUB_CATEGORY.KNOWN.TMP_FILES)
            .addRule(`AssertionError`, `*/tmp/*`)

          .setSubCategory(this.SUB_CATEGORY.KNOWN.SYNC_SKIP)
            .addRule(`CypressError`, `*sync skip; aborting execution*`)

          .setSubCategory(this.SUB_CATEGORY.KNOWN.EMAIL_SUBJECT)
            .addRule(`Error`, `*Subject line does not match name*`)
            .addRule(`AssertionError`, `*Subject line should contain claimant name*`)

          .setSubCategory(this.SUB_CATEGORY.KNOWN.DOWNLOADS)
            .addRule(`CypressError`, `*cy.task('getNoticeFileName')*`)
    /**
     * Notification Issues
     */
        .setCategory(this.CATEGORY.NOTIFICATION)
          .addRule(`CypressError`, `*cy.task('getEmails')*`)

        .done();
    /*ignore jslint end*/
  }

  matchRuleExpl(str, rule) {
    // for this solution to work on any string, no matter what characters it has
    var escapeRegex = (str) =>
      str.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");

    // "."  => Find a single character, except newline or line terminator
    // ".*" => Matches any string that contains zero or more characters
    rule = rule.split("*").map(escapeRegex).join(".*");

    // "^"  => Matches any string with the following at the beginning of it
    // "$"  => Matches any string with that in front at the end of it
    rule = "^" + rule + "$";

    //Create a regular expression object for matching string
    var regex = new RegExp(rule);

    //Returns true if it finds a match, otherwise it returns false
    return regex.test(str);
  }

  setErrorCategory(event) {
    event.category = null;
    event.subCategory = null;

    for (const rule of this.RuleBuilder.rules) {
      if (
        rule.errorClass === event.errorClass &&
        this.matchRuleExpl(event.errorMessage, rule.errorMessage)
      ) {
        event.category = rule.category;
        event.subCategory = rule.subCategory;
        break;
      }
    }

    return event;
  }
}

class RuleBuilder {
  constructor() {
    this.rules = [];
    this.category = null;
    this.subCategory = null;
  }

  setCategory(category) {
    this.category = category;
    this.subCategory = null;
    return this;
  }

  setSubCategory(subCategory) {
    this.subCategory = subCategory;
    return this;
  }

  addRule(errorClass, errorMessage) {
    this.rules.push({
      errorClass: errorClass,
      errorMessage: errorMessage,
      category: this.category,
      subCategory: this.subCategory,
    });
    return this;
  }

  done() {
    return this.rules;
  }
}

module.exports = {
  ErrorCategory,
  RuleBuilder,
};

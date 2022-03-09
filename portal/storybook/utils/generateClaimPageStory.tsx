import { chain, get, upperFirst } from "lodash";
import BenefitsApplication from "src/models/BenefitsApplication";
import React from "react";
import User from "../../src/models/User";
import { ValidationError } from "src/errors";
import { createMockBenefitsApplication } from "lib/mock-helpers/createMockBenefitsApplication";
import englishLocale from "src/locales/app/en-US";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

/**
 * Generates the config and story components for a claims page.
 * @param {string} claimsPageSubpath The path to the story
 * @param {object.<string, Claim>} [mockClaims] A dictionary of mock Claim objects that a user can select from the storybook
 *    "claim" control. The keys of the dictionary are the radio options.
 * @returns {{ config: {title: string, component: React.Component}, DefaultStory: React.Component }}
 *
 * @example
 * generateClaimPageStory("name", {
 *   empty: new BenefitsApplication(),
 *   "with name": new BenefitsApplication({
 *     first_name: "Jane",
 *     middle_name: "N", last_name:
 *     "Doe"
 *   }),
 * })
 */
export default function generateClaimPageStory(
  claimsPageSubpath: string,
  mockClaims: { [scenario: string]: BenefitsApplication } | null = null
) {
  // e.g. applications/leave-duration --> LeaveDuration
  const componentName = chain(claimsPageSubpath)
    .split("/")
    .last()
    .camelCase()
    .upperFirst()
    .value();
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const module = require(`src/pages/applications/${claimsPageSubpath}`);
  const Component = module[componentName];
  const fields = module.fields || [];

  const possibleErrors = getPossibleErrors(fields, englishLocale.translation);
  const config = generateConfig(claimsPageSubpath, Component);
  const DefaultStory = generateDefaultStory(
    Component,
    mockClaims,
    possibleErrors
  );

  return { config, DefaultStory };
}

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'claimsPageSubpath' implicitly has an 'a... Remove this comment to see the full error message
function generateConfig(claimsPageSubpath, Component) {
  const title = claimsPageSubpath
    .split("/")
    .map(kebabCaseToTitleCase)
    .join("/");
  return {
    title: `Pages/Applications/${title}`, // we could capitalize the path parts if we wanted to
    component: Component,
  };
}

/**
 * Generate storybook story for the claim page component.
 * Configurable with mock claims and possible validation errors.
 * @param {React.Component} Component
 * @param {BenefitsApplication[]} mockClaims
 * @param {ErrorInfo[]} possibleErrors
 * @returns {React.Component} Storybook story component
 */
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'Component' implicitly has an 'any' type... Remove this comment to see the full error message
function generateDefaultStory(Component, mockClaims, possibleErrors) {
  let claims = mockClaims;

  if (!claims) {
    // Customize mock claims for different stories
    switch (Component.displayName) {
      // Pages contextualized based on leave type
      case "ConcurrentLeaves":
        claims = {
          "continuous leave": createMockBenefitsApplication("continuous"),
          "continuous reduced leave": createMockBenefitsApplication(
            "continuous",
            "reducedSchedule"
          ),
          "intermittent leave": createMockBenefitsApplication("intermittent"),
          "reduced leave": createMockBenefitsApplication("reducedSchedule"),
        };
        break;

      default:
        claims = {
          // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
          empty: new BenefitsApplication(),
        };
    }
  }

  // Just take the first claim in the list of claims as the defaultClaim
  const defaultClaim = Object.keys(claims)[0];

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
  const DefaultStory = (args) => {
    const errorDisplayStrs = args.errors || [];
    const claim = claims[args.claim || defaultClaim];
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    const user = new User();
    const issues =
      // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'displayStr' implicitly has an 'any' typ... Remove this comment to see the full error message
      errorDisplayStrs.map((displayStr) => {
        const errorInfo = possibleErrors.find(
          // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'error' implicitly has an 'any'
          (error) => error.displayStr === displayStr
        );
        return { ...errorInfo, namespace: "applications" };
      });

    const appLogic = useMockableAppLogic({
      errors: [new ValidationError(issues)],
    });

    return (
      <Component
        appLogic={appLogic}
        claim={claim}
        user={user}
        documents={appLogic.documents.documents.items}
        query={{ claim_id: claim.application_id }}
      />
    );
  };

  DefaultStory.args = {
    claim: defaultClaim,
  };

  DefaultStory.argTypes = {
    claim: {
      control: {
        type: "radio",
        options: Object.keys(claims),
      },
    },
    errors: {
      control: {
        type: "check",
        // @ts-expect-error FIXME: err is `any`
        options: possibleErrors.map((error) => error.displayStr),
      },
    },
  };

  return DefaultStory;
}

/**
 * Error info object
 * @typedef {object} ErrorInfo
 * @property {string} displayStr String used to display the storybook option
 * @property {string} field Claim field
 * @property {string} i18nKey I18n key for the error
 * @property {string} type Error type
 */

/**
 * Given a list of fields, returns a list of possible errors
 * @param {string[]} fields Array of fields
 * @param {*} translation Translation strings object
 * @returns {ErrorInfo[]}
 */
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'fields' implicitly has an 'any' type.
function getPossibleErrors(fields, translation) {
  // @ts-expect-error ts-migrate(7034) FIXME: Variable 'possibleErrors' implicitly has type 'any... Remove this comment to see the full error message
  let possibleErrors = [];
  for (const field of fields) {
    const claimField = field.substring("claim.".length);
    // @ts-expect-error ts-migrate(7005) FIXME: Variable 'possibleErrors' implicitly has an 'any[]... Remove this comment to see the full error message
    possibleErrors = possibleErrors.concat(
      getPossibleErrorsForField(claimField, translation)
    );
  }
  return possibleErrors;
}

/**
 * Returns a list of possible errors for a given claim field
 * @param {string} field Claim field path
 * @param {*} translation Translation strings object
 * @returns {ErrorInfo} I18n keys for the various error types that are associated with the field
 */
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'field' implicitly has an 'any' type.
function getPossibleErrorsForField(field, translation) {
  // Remove array indexes from the field since i18n keys don't depend on array indexes
  // i.e. convert foo[0].bar[1].cat to foo.bar.cat
  const claimFieldKey = field.replace(/\[(\d+)\]/g, "");
  const errorTypes = Object.keys(
    get(translation.errors.applications, claimFieldKey) || {}
  );
  const possibleErrors = errorTypes.map((type) => {
    return {
      displayStr: `${claimFieldKey}: ${type}`,
      field,
      type,
    };
  });
  return possibleErrors;
}

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'str' implicitly has an 'any' type.
function kebabCaseToTitleCase(str) {
  return (
    str
      .split("-")
      // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'word' implicitly has an 'any' type.
      .map((word) => upperFirst(word))
      .join(" ")
  );
}

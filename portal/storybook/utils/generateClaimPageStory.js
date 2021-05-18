import { chain, find, first, get, map, upperFirst } from "lodash";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import DocumentCollection from "src/models/DocumentCollection";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";
import User from "../../src/models/User";
import englishLocale from "src/locales/app/en-US";
import { useTranslation } from "src/locales/i18n";

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
  claimsPageSubpath,
  mockClaims = null
) {
  // e.g. applications/leave-duration --> LeaveDuration
  const componentName = chain(claimsPageSubpath)
    .split("/")
    .last()
    .camelCase()
    .upperFirst()
    .value();
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
function generateDefaultStory(Component, mockClaims, possibleErrors) {
  if (!mockClaims) {
    mockClaims = {
      empty: new BenefitsApplication(),
      "continuous leave": new MockBenefitsApplicationBuilder()
        .continuous()
        .create(),
    };
  }

  // Just take the first claim in the list of mockClaims as the defaultClaim
  const defaultClaim = first(Object.entries(mockClaims))[0];

  const DefaultStory = (args) => {
    const errorDisplayStrs = args.errors || [];
    const claim = mockClaims[args.claim || defaultClaim];
    const user = new User();
    const { t } = useTranslation();
    const appErrors = new AppErrorInfoCollection(
      errorDisplayStrs.map((displayStr) => {
        const errorInfo = find(possibleErrors, { displayStr });
        const { field, i18nKey } = errorInfo;
        return new AppErrorInfo({
          message: t(i18nKey),
          name: "ValidationError",
          field,
        });
      })
    );
    const appLogic = {
      benefitsApplications: {
        update: () => {},
      },
      documents: {
        attachDocument: () => {},
        documents: new DocumentCollection([]),
      },
      appErrors,
      setAppErrors: () => {},
    };
    return (
      <Component
        appLogic={appLogic}
        claim={claim}
        user={user}
        documents={appLogic.documents.documents.items}
        query={{}}
      />
    );
  };

  DefaultStory.argTypes = {
    claim: {
      defaultValue: defaultClaim,
      control: {
        type: "radio",
        options: Object.keys(mockClaims),
      },
    },
    errors: {
      control: {
        type: "check",
        options: map(possibleErrors, "displayStr"),
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
function getPossibleErrors(fields, translation) {
  let possibleErrors = [];
  for (const field of fields) {
    const claimField = field.substring("claim.".length);
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
function getPossibleErrorsForField(field, translation) {
  // Remove array indexes from the field since i18n keys don't depend on array indexes
  // i.e. convert foo[0].bar[1].cat to foo.bar.cat
  const claimFieldKey = field.replace(/\[(\d+)\]/g, "");
  const errorTypes = Object.keys(
    get(translation.errors.claims, claimFieldKey) || {}
  );
  const possibleErrors = errorTypes.map((type) => {
    return {
      displayStr: `${claimFieldKey}: ${type}`,
      field,
      i18nKey: `errors.claims.${claimFieldKey}.${type}`,
      type,
    };
  });
  return possibleErrors;
}

function kebabCaseToTitleCase(str) {
  return str
    .split("-")
    .map((word) => upperFirst(word))
    .join(" ");
}

import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import Claim from "src/models/Claim";
import React from "react";
import User from "../../src/models/User";
import _ from "lodash";
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
 *   empty: new Claim(),
 *   "with name": new Claim({
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
  // e.g. claims/leave-duration --> LeaveDuration
  const componentName = _.chain(claimsPageSubpath)
    .split("/")
    .last()
    .camelCase()
    .upperFirst()
    .value();
  const module = require(`src/pages/claims/${claimsPageSubpath}`);
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
    title: `Pages/Claims/${title}`, // we could capitalize the path parts if we wanted to
    component: Component,
  };
}

function generateDefaultStory(Component, mockClaims, possibleErrors) {
  if (!mockClaims) {
    mockClaims = {
      empty: new Claim(),
    };
  }

  // Just take the first claim in the list of mockClaims as the defaultClaim
  const defaultClaim = _.first(Object.entries(mockClaims))[0];

  const DefaultStory = (args) => {
    const errors = args.errors || [];
    const claim = mockClaims[args.claim || defaultClaim];
    const user = new User();
    const { t } = useTranslation();
    const appErrors = new AppErrorInfoCollection(
      errors.map((error) => {
        const field = error.substring(0, error.lastIndexOf("."));
        return new AppErrorInfo({
          message: t(`errors.claims.${error}`),
          name: "ValidationError",
          field,
        });
      })
    );
    const appLogic = {
      claims: {
        update: () => {},
      },
      appErrors,
    };
    return <Component appLogic={appLogic} claim={claim} user={user} />;
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
        options: possibleErrors,
      },
    },
  };

  return DefaultStory;
}

function getPossibleErrors(fields, translation) {
  const possibleErrors = [];
  for (const field of fields) {
    const claimField = field.substring("claim.".length);
    for (const type in _.get(translation.errors.claims, claimField)) {
      possibleErrors.push(`${claimField}.${type}`);
    }
  }
  return possibleErrors;
}

function kebabCaseToTitleCase(str) {
  return str
    .split("-")
    .map((word) => _.upperFirst(word))
    .join(" ");
}

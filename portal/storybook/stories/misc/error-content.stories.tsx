import Alert from "src/components/core/Alert";
import Heading from "src/components/core/Heading";
import React from "react";
import englishLocale from "src/locales/app/en-US";
import { groupBy } from "lodash";
import { useTranslation } from "react-i18next";

export default {
  title: "Misc/Error content",
  parameters: {
    viewMode: "docs",
  },
};

export const Default = () => {
  const { t } = useTranslation();
  const flatMessageKeyList = getMessageKeys(
    englishLocale.translation.errors,
    "errors."
  );

  // Group by the root key so we can render group headings
  const messageGroups = groupBy(flatMessageKeyList, (key) => {
    const groupName = key.split(".")[1];

    if (groupName.startsWith("caughtError")) return "caughtError";
    if (groupName.startsWith("invalidFile")) return "invalidFile";

    return groupName;
  });

  /**
   * Scroll to relevant section of the errors list.
   * We could use anchor links for this, however clicking these in Storybook
   * results in the link being opened in a new window, instead of actually
   * scrolling to the relevant section, so we're doing it this way instead:
   * @param {object} event
   */

  const handleListItemClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    if (event.target instanceof HTMLElement) {
      const id = event.target.getAttribute("data-target");
      if (!id) return;
      document.querySelector(id)?.scrollIntoView();
    }
  };

  return (
    <div className="measure-6">
      {/* Table of contents */}
      <Heading level="2">Message groups</Heading>
      <ul className="usa-list">
        {Object.keys(messageGroups).map((groupPath) => (
          <li key={groupPath}>
            <button
              className="usa-button usa-button--unstyled"
              type="button"
              data-target={`#${groupPath}`}
              onClick={handleListItemClick}
            >
              {groupPath}
            </button>
          </li>
        ))}
      </ul>

      {Object.entries(messageGroups).map(([groupPath, messageKeys]) => {
        return (
          <section
            className="margin-top-6 padding-top-6 border-top-2px border-top-base"
            id={groupPath}
            key={groupPath}
          >
            <Heading level="2">{groupPath}</Heading>

            {messageKeys.map((messageKey) => (
              <div key={messageKey}>
                <code className="font-code-2xs text-base">{messageKey}</code>
                <Alert className="margin-bottom-3" aria-label={messageKey}>
                  {t(messageKey)}
                </Alert>
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
};

function getMessageKeys(
  messages: { [key: string]: unknown },
  keyPrefix = ""
): string[] {
  const keys = Object.entries(messages)
    .map(([key, value]) => {
      const keyPath = `${keyPrefix}${key}`;
      if (typeof value === "string") return keyPath;
      return getMessageKeys(value as { [key: string]: unknown }, `${keyPath}.`);
    })
    .flat();

  return keys;
}

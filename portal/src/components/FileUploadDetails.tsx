import Details from "./Details";
import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

/**
 * A pre-populated Details component with information about uploading files. This component is
 * intended to be used on pages which use one or more FileCardList components.
 */
function FileUploadDetails() {
  const { t } = useTranslation();
  const tipsArray = t("components.fileUploadDetails.tips", {
    returnObjects: true,
  });
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'map' does not exist on type 'string'.
  const renderedTips = tipsArray.map((list, index) => (
    <List key={index} list={list} />
  ));

  return (
    <Details label={t("components.fileUploadDetails.label")}>
      <div>{renderedTips}</div>
    </Details>
  );
}

// Renders a list of text strings with a heading above the list
function List(props) {
  const list = props.list;

  return (
    <React.Fragment>
      <Heading level="2" size="4">
        {list.listHeading}
      </Heading>
      <ul className="usa-list">
        {list.listItems.map((listItem, index) => (
          <li key={index}>{listItem}</li>
        ))}
      </ul>
    </React.Fragment>
  );
}

List.propTypes = {
  list: PropTypes.shape({
    listHeading: PropTypes.string.isRequired,
    listItems: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  }).isRequired,
};

export default FileUploadDetails;

import Details from "./Details";
import Heading from "./Heading";
import React from "react";
import { useTranslation } from "../locales/i18n";

interface TipListContent {
  listHeading: string;
  listItems: string[];
}

interface ListProps {
  list: TipListContent;
}

/**
 * A pre-populated Details component with information about uploading files. This component is
 * intended to be used on pages which use one or more FileCardList components.
 */
function FileUploadDetails() {
  const { t } = useTranslation();
  const tipsArray = t<string, TipListContent[]>(
    "components.fileUploadDetails.tips",
    {
      returnObjects: true,
    }
  );
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
function List(props: ListProps) {
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

export default FileUploadDetails;

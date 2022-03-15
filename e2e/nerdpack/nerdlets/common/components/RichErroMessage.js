import React from "react";

const httpUrlRegex = new RegExp(
  /(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\\+.~#?&//=]*)/
);

export default function RichErroMessage({ children }) {
  return (
    <>
      {React.Children.map(children, (errorMessage) => {
        if (typeof errorMessage !== "string") {
          return errorMessage;
        }
        return errorMessage.split(httpUrlRegex).map((substring) => {
          if (httpUrlRegex.test(substring)) {
            return (
              <a href={encodeURI(substring)} target="_blank">
                {substring}
              </a>
            );
          }
          return substring;
        });
      })}
    </>
  );
}

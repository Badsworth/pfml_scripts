import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import User from "../../models/User";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Welcome = ({ appLogic, user }) => {
  const { t } = useTranslation();

  const adminPages = [];
  for (const [k, v] of Object.entries(routes.admin)) {
    adminPages.push({ name: k, path: v });
  }
  console.log(adminPages);

  return (
    <React.Fragment>
      <div className="grid-row">
        <div className="desktop:grid-col">
          <Title>{t("pages.adminWelcome.title")}</Title>
          <div>{t("pages.adminWelcome.body")}</div>
          <div className="margin-top-2">
            {adminPages.map((p) => (
              <Link key={p.name} href={p.path}>
                <a className="display-inline-block margin-left-1">{p.name}</a>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </React.Fragment>
  );
};

Welcome.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
};

export default withUser(Welcome);

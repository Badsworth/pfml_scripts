import * as api from "../api";

import { useRef, useState } from "react";

import { ChevronLeftIcon } from "@heroicons/react/solid";
import Link from "next/link";
import { LoadingState } from "../../src/pages/_app";
import PFMLLogo from "./PFMLLogo";
import classNames from "classnames";
import { logout } from "../../src/utils/azure_sso_authorization";

export type Props = {
  user: api.AdminUserResponse | null;
  setUser: React.Dispatch<React.SetStateAction<api.AdminUserResponse | null>>;
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >;
  loadingState: LoadingState;
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>;
};

const Header = ({
  user,
  setError,
  setUser,
  loadingState,
  setLoadingState,
}: Props) => {
  const [dropdownIsOpen, setDropdownIsOpen] = useState<boolean>(false);

  const dropdown = useRef<HTMLElement>(null);
  let mouseTimer: ReturnType<typeof setTimeout>;

  const toggleDropdown = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();

    if (e.type == "click") {
      setDropdownIsOpen(!dropdownIsOpen);
    } else {
      if (dropdownIsOpen) {
        // Give user a half second delay on mouseout
        resetMouseTimer(e);
        mouseTimer = setTimeout(() => {
          setDropdownIsOpen(false);
        }, 500);
      }
    }
  };

  const dropdownBlur = (e: React.FocusEvent<HTMLElement>) => {
    if (!dropdown.current?.contains(e.relatedTarget as Node)) {
      setDropdownIsOpen(false);
    }
  };

  const resetMouseTimer = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();

    clearTimeout(mouseTimer);
  };

  const handleLogout = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();

    logout(setError, setUser, loadingState, setLoadingState);
  };

  const firstInitial = user?.first_name?.charAt(0);
  const lastInitial = user?.last_name?.charAt(0);

  return (
    <header className="page__header">
      <div className="page__logo">
        <Link href="/">
          <a
            title="Paid Family & Medical Leave - Massachusetts"
            className="page__logo-link"
          >
            <PFMLLogo className="pfml-logo-header" />
          </a>
        </Link>
      </div>
      {user && (
        <div className="page__user-options">
          <span
            className={classNames("user-options", {
              "user-options--open": dropdownIsOpen,
            })}
            onMouseEnter={resetMouseTimer}
            onMouseLeave={toggleDropdown}
            onBlur={dropdownBlur}
            ref={dropdown}
            data-testid="user-options"
          >
            <a
              href="#"
              role="button"
              className="user-options__trigger"
              aria-label={`${user?.first_name} ${user?.last_name} - User Options`}
              onClick={toggleDropdown}
              data-testid="user-options-trigger"
              aria-controls="user-options__dropdown"
            >
              <span className="user-options__avatar">
                {firstInitial}
                {lastInitial}
              </span>
              <span className="user-options__name">
                {user?.first_name} {user?.last_name}
              </span>
              <ChevronLeftIcon className="user-options__trigger-icon" />
            </a>
            {dropdownIsOpen && (
              <ul
                id="user-options__dropdown"
                className="user-options__dropdown"
                tabIndex={-1}
                data-testid="user-options-dropdown"
              >
                <li className="user-options__dropdown-item user-options__dropdown-item--border">
                  Signed in as <strong>{user?.email_address}</strong>
                </li>
                <li className="user-options__dropdown-item">
                  <a href="#" className="user-option" onClick={handleLogout}>
                    Sign out
                  </a>
                </li>
              </ul>
            )}
          </span>
        </div>
      )}
    </header>
  );
};

export default Header;

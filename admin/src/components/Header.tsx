import Image from "next/image";
import Link from "next/link";

export default function Header() {
  return (
    <header className="page__header">
      <div className="page__logo">
        <Link href="/">
          <a
            title="Paid Family & Medical Leave - Massachusetts"
            className="page__logo-link"
          ></a>
        </Link>
      </div>
      <div className="page__user-options">
        <a
          href="#"
          role="button"
          aria-label="FirstName LastName - User Options"
          className="user-options"
        >
          <span className="user-options__avatar">
            <Image
              className="user-options__avatar-image"
              src="https://via.placeholder.com/32"
              alt="FirstName LastName"
              height="32px"
              width="32px"
            />
          </span>
          <span className="user-options__name">FirstName LastName</span>
          <span className="user-options__dropdown"></span>
        </a>
      </div>
    </header>
  );
}

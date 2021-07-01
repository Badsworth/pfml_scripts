export default function Sidebar() {
	return (
		<aside className="page__sidebar">
			<nav className="menu">
				<ul className="menu__list">
					<li className="menu__list-item">
						<a href="#" className="menu__link">
							Nav Item One
						</a>
					</li>
					<li className="menu__list-item">
						<a href="#" className="menu__link">
							Nav Item Two
						</a>
					</li>
					<li className="menu__list-item">
						<a href="#" className="menu__link">
							Nav Item Three
						</a>
					</li>
				</ul>
			</nav>
			<div className="settings">
				<ul className="settings__list">
					<li className="settings__list-item">
						<a href="#" className="settings__link">
							Settings
						</a>
					</li>
					<li className="settings__list-item">
						<a href="#" className="settings__link">
							Help
						</a>
					</li>
				</ul>
			</div>
			<div className="environment">
				<div className="environment__label">Environment</div>
				<div className="environment__flag">Production</div>
			</div>
		</aside>
	);
}

import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="layout">
      <nav className="nav-bar">
        <span className="nav-logo">GSD</span>
        <div className="nav-tabs">
          <NavLink
            to="/engage"
            className={({ isActive }) =>
              `nav-tab ${isActive ? "nav-tab--active" : ""}`
            }
          >
            Engage
          </NavLink>
          <NavLink
            to="/intake"
            className={({ isActive }) =>
              `nav-tab ${isActive ? "nav-tab--active" : ""}`
            }
          >
            Intake
          </NavLink>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

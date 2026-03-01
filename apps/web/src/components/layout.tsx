import { NavLink, Outlet } from 'react-router-dom'

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'nav-link nav-link-active' : 'nav-link'

export function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">OpenBB Signal Deck</div>
        <nav className="nav">
          <NavLink to="/" className={navClass} end>
            Dashboard
          </NavLink>
          <NavLink to="/feed" className={navClass}>
            Feed Stream
          </NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}

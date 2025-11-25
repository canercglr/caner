import React, { useState, useEffect } from 'react'
import { gsap } from 'gsap'
import './Navbar.css'

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    gsap.fromTo('.nav-item',
      { y: -20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, delay: 2.2, ease: 'power2.out' }
    )
  }, [])

  const navItems = [
    { label: 'Teknikler', href: '#techniques' },
    { label: 'Viral Vektörler', href: '#viral-vectors' },
    { label: 'Tracing', href: '#tracing' },
    { label: 'Davranış', href: '#behavior' },
    { label: 'Görüntüleme', href: '#imaging' }
  ]

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        <a href="#" className="navbar-logo nav-item">
          <span className="logo-icon">
            <svg viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" stroke="url(#logoGradient)" strokeWidth="2" />
              <circle cx="20" cy="20" r="8" fill="url(#logoGradient)" />
              <circle cx="12" cy="14" r="3" fill="#22d3ee" />
              <circle cx="28" cy="14" r="3" fill="#a855f7" />
              <circle cx="20" cy="28" r="3" fill="#ec4899" />
              <line x1="20" y1="20" x2="12" y2="14" stroke="#22d3ee" strokeWidth="1.5" />
              <line x1="20" y1="20" x2="28" y2="14" stroke="#a855f7" strokeWidth="1.5" />
              <line x1="20" y1="20" x2="20" y2="28" stroke="#ec4899" strokeWidth="1.5" />
              <defs>
                <linearGradient id="logoGradient" x1="0" y1="0" x2="40" y2="40">
                  <stop stopColor="#6366f1" />
                  <stop offset="0.5" stopColor="#a855f7" />
                  <stop offset="1" stopColor="#ec4899" />
                </linearGradient>
              </defs>
            </svg>
          </span>
          <span className="logo-text">NeuroTR</span>
        </a>

        <ul className={`navbar-menu ${menuOpen ? 'open' : ''}`}>
          {navItems.map((item, index) => (
            <li key={index} className="nav-item">
              <a href={item.href} onClick={() => setMenuOpen(false)}>
                {item.label}
              </a>
            </li>
          ))}
        </ul>

        <button
          className="navbar-toggle nav-item"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <span className={`toggle-line ${menuOpen ? 'open' : ''}`}></span>
          <span className={`toggle-line ${menuOpen ? 'open' : ''}`}></span>
        </button>
      </div>
    </nav>
  )
}

export default Navbar

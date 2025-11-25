import React, { useRef, useEffect } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import './Footer.css'

gsap.registerPlugin(ScrollTrigger)

const Footer = () => {
  const footerRef = useRef()

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.footer-content',
        { y: 50, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: footerRef.current,
            start: 'top 90%',
            toggleActions: 'play none none reverse'
          }
        }
      )
    }, footerRef)

    return () => ctx.revert()
  }, [])

  const techniques = [
    'Optogenetik',
    'Kemogenetik',
    'Fiber Fotometri',
    'Elektrofizyoloji',
    'GRAB Sensörleri'
  ]

  const viralVectors = [
    'AAV',
    'Rabies',
    'PRV',
    'HSV',
    'CAV-2'
  ]

  const resources = [
    'Tracing Metodları',
    'Davranış Testleri',
    'Görüntüleme',
    'Protokoller',
    'Kaynaklar'
  ]

  return (
    <footer ref={footerRef} className="footer">
      <div className="footer-gradient"></div>

      <div className="container">
        <div className="footer-content">
          <div className="footer-main">
            <div className="footer-brand">
              <div className="footer-logo">
                <svg viewBox="0 0 40 40" fill="none">
                  <circle cx="20" cy="20" r="18" stroke="url(#footerGradient)" strokeWidth="2" />
                  <circle cx="20" cy="20" r="8" fill="url(#footerGradient)" />
                  <circle cx="12" cy="14" r="3" fill="#22d3ee" />
                  <circle cx="28" cy="14" r="3" fill="#a855f7" />
                  <circle cx="20" cy="28" r="3" fill="#ec4899" />
                  <line x1="20" y1="20" x2="12" y2="14" stroke="#22d3ee" strokeWidth="1.5" />
                  <line x1="20" y1="20" x2="28" y2="14" stroke="#a855f7" strokeWidth="1.5" />
                  <line x1="20" y1="20" x2="20" y2="28" stroke="#ec4899" strokeWidth="1.5" />
                  <defs>
                    <linearGradient id="footerGradient" x1="0" y1="0" x2="40" y2="40">
                      <stop stopColor="#6366f1" />
                      <stop offset="0.5" stopColor="#a855f7" />
                      <stop offset="1" stopColor="#ec4899" />
                    </linearGradient>
                  </defs>
                </svg>
                <span>NeuroTR</span>
              </div>
              <p className="footer-description">
                Türkiye'nin en kapsamlı sinirbilim teknikler platformu.
                Modern nörobilim metodlarını interaktif olarak keşfedin.
              </p>
              <div className="footer-cta">
                <a href="#techniques" className="footer-btn">
                  Keşfetmeye Başla
                </a>
              </div>
            </div>

            <div className="footer-links">
              <div className="footer-column">
                <h4>Teknikler</h4>
                <ul>
                  {techniques.map((item, i) => (
                    <li key={i}><a href="#techniques">{item}</a></li>
                  ))}
                </ul>
              </div>

              <div className="footer-column">
                <h4>Viral Vektörler</h4>
                <ul>
                  {viralVectors.map((item, i) => (
                    <li key={i}><a href="#viral-vectors">{item}</a></li>
                  ))}
                </ul>
              </div>

              <div className="footer-column">
                <h4>Kaynaklar</h4>
                <ul>
                  {resources.map((item, i) => (
                    <li key={i}><a href="#tracing">{item}</a></li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <div className="footer-info">
              <p>© 2024 NeuroTR. Türkiye Sinirbilim Topluluğu için geliştirildi.</p>
            </div>
            <div className="footer-social">
              <a href="#" className="social-link" aria-label="Twitter">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </a>
              <a href="#" className="social-link" aria-label="GitHub">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
                </svg>
              </a>
              <a href="#" className="social-link" aria-label="LinkedIn">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="footer-glow"></div>
    </footer>
  )
}

export default Footer

import React, { Suspense, useEffect, useState } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import TechniquesSection from './components/TechniquesSection'
import ViralVectorsSection from './components/ViralVectorsSection'
import TracingSection from './components/TracingSection'
import BehaviorSection from './components/BehaviorSection'
import ImagingSection from './components/ImagingSection'
import Footer from './components/Footer'
import Cursor from './components/Cursor'
import './styles/App.css'

gsap.registerPlugin(ScrollTrigger)

function App() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false)
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!loading) {
      gsap.fromTo('.app-content',
        { opacity: 0 },
        { opacity: 1, duration: 1, ease: 'power2.out' }
      )
    }
  }, [loading])

  if (loading) {
    return (
      <div className="loader">
        <div className="loader-content">
          <div className="loader-brain">
            <svg viewBox="0 0 100 100" className="brain-svg">
              <defs>
                <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="50%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
              <path
                className="brain-path"
                fill="none"
                stroke="url(#brainGradient)"
                strokeWidth="2"
                d="M50 10 Q70 10 75 25 Q85 25 85 40 Q95 45 90 55 Q95 65 85 70 Q85 85 70 85 Q65 95 50 90 Q35 95 30 85 Q15 85 15 70 Q5 65 10 55 Q5 45 15 40 Q15 25 25 25 Q30 10 50 10"
              />
              <circle className="neuron-pulse" cx="50" cy="50" r="3" fill="#22d3ee" />
            </svg>
          </div>
          <h2 className="loader-text">NeuroTR</h2>
          <p className="loader-subtext">Sinirbilim Dünyasına Hoş Geldiniz</p>
          <div className="loader-bar">
            <div className="loader-bar-fill"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="noise"></div>
      <Cursor />
      <div className="app-content">
        <Navbar />
        <main>
          <Hero />
          <TechniquesSection />
          <ViralVectorsSection />
          <TracingSection />
          <BehaviorSection />
          <ImagingSection />
        </main>
        <Footer />
      </div>
    </div>
  )
}

export default App

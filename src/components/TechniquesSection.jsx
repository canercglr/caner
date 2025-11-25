import React, { useRef, useEffect, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, MeshDistortMaterial } from '@react-three/drei'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import * as THREE from 'three'
import './TechniquesSection.css'

gsap.registerPlugin(ScrollTrigger)

function TechniqueModel({ color, speed = 2 }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.3
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.2
    }
  })

  return (
    <Float speed={speed} rotationIntensity={0.5}>
      <mesh ref={meshRef}>
        <torusKnotGeometry args={[0.8, 0.3, 100, 16]} />
        <MeshDistortMaterial
          color={color}
          transparent
          opacity={0.8}
          distort={0.3}
          speed={2}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
    </Float>
  )
}

const techniques = [
  {
    id: 'optogenetics',
    title: 'Optogenetik',
    subtitle: 'Işıkla Nöron Kontrolü',
    color: '#22d3ee',
    icon: '💡',
    description: 'Işığa duyarlı proteinler (opsınlar) kullanarak nöronları milisaniye hassasiyetinde aktive veya inhibe etme tekniği.',
    details: [
      'Channelrhodopsin-2 (ChR2) - Mavi ışıkla aktivasyon',
      'Halorhodopsin (NpHR) - Sarı ışıkla inhibisyon',
      'Archaerhodopsin (Arch) - Yeşil ışıkla inhibisyon',
      'Fiber optik implantlar ile in vivo kullanım',
      'Davranışsal paradigmalarla kombinasyon'
    ],
    applications: ['Nöral devre haritalama', 'Davranış modülasyonu', 'Hafıza çalışmaları', 'Motor kontrol araştırmaları']
  },
  {
    id: 'chemogenetics',
    title: 'Kemogenetik',
    subtitle: 'DREADD Teknolojisi',
    color: '#a855f7',
    icon: '🧬',
    description: 'Designer Receptors Exclusively Activated by Designer Drugs (DREADDs) ile kimyasal moleküller kullanarak nöron aktivitesini uzaktan kontrol etme.',
    details: [
      'hM3Dq - Gq-coupled aktivatör DREADD',
      'hM4Di - Gi-coupled inhibitör DREADD',
      'CNO (Clozapine N-oxide) ligand',
      'Deschloroclozapine (DCZ) - yeni nesil ligand',
      'Saatler süren uzun süreli modülasyon'
    ],
    applications: ['Kronik nöral modülasyon', 'Davranış testleri', 'Uzun vadeli devre manipülasyonu', 'Translasyonel araştırmalar']
  },
  {
    id: 'fiber-photometry',
    title: 'Fiber Fotometri',
    subtitle: 'Gerçek Zamanlı Nöral Dinamikler',
    color: '#10b981',
    icon: '📊',
    description: 'Genetik olarak kodlanmış sensörler kullanarak serbest hareket eden hayvanlarda nörotransmitter ve kalsiyum dinamiklerini gerçek zamanlı izleme.',
    details: [
      'GCaMP serisi - Kalsiyum göstergeleri',
      'dLight - Dopamin sensörü',
      'GRABNE - Norepinefrin sensörü',
      'iGluSnFR - Glutamat sensörü',
      'Bulk florometri ve tek-fiber kayıtlar'
    ],
    applications: ['Davranış sırasında nöral aktivite', 'Nörotransmitter salınımı', 'Ödül ve motivasyon', 'Stres yanıtları']
  },
  {
    id: 'electrophysiology',
    title: 'Ex Vivo Elektrofizyoloji',
    subtitle: 'Beyin Kesiti Kayıtları',
    color: '#f97316',
    icon: '⚡',
    description: 'Akut beyin kesitlerinde patch-clamp ve field recording teknikleri ile sinaptik iletim ve nöronal özelliklerin detaylı analizi.',
    details: [
      'Whole-cell patch clamp',
      'Field EPSP/IPSP kayıtları',
      'LTP/LTD plastisitite protokolleri',
      'Current ve voltage clamp modları',
      'Optogenetik stimülasyon kombinasyonu'
    ],
    applications: ['Sinaptik plastisite', 'İyon kanalı karakterizasyonu', 'İlaç etki mekanizmaları', 'Nöronal özellikler']
  },
  {
    id: 'grab-sensors',
    title: 'GRAB Sensörleri',
    subtitle: 'Yeni Nesil Nörotransmitter Algılayıcıları',
    color: '#ec4899',
    icon: '🔬',
    description: 'GPCR-Activation Based sensörler ile spesifik nörotransmitterlerin yüksek uzaysal ve zamansal çözünürlükle görüntülenmesi.',
    details: [
      'GRABDA - Dopamin sensörü',
      'GRAB5HT - Serotonin sensörü',
      'GRABNE - Norepinefrin sensörü',
      'GRABACh - Asetilkolin sensörü',
      'Yüksek sinyal-gürültü oranı'
    ],
    applications: ['Nöromodülasyon çalışmaları', 'İki-foton görüntüleme', 'Fiber fotometri', 'Sinaptik salınım dinamikleri']
  }
]

const TechniqueCard = ({ technique, index, isActive, onClick }) => {
  const cardRef = useRef()

  useEffect(() => {
    gsap.fromTo(cardRef.current,
      { y: 50, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.8,
        delay: index * 0.1,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: cardRef.current,
          start: 'top 85%',
          toggleActions: 'play none none reverse'
        }
      }
    )
  }, [index])

  return (
    <div
      ref={cardRef}
      className={`technique-card ${isActive ? 'active' : ''}`}
      onClick={() => onClick(technique.id)}
      style={{ '--accent-color': technique.color }}
    >
      <div className="card-glow" style={{ background: technique.color }}></div>
      <div className="card-icon">{technique.icon}</div>
      <h3 className="card-title">{technique.title}</h3>
      <p className="card-subtitle">{technique.subtitle}</p>
      <div className="card-arrow">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
      </div>
    </div>
  )
}

const TechniqueDetail = ({ technique }) => {
  const detailRef = useRef()

  useEffect(() => {
    if (technique) {
      gsap.fromTo(detailRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
      )
    }
  }, [technique])

  if (!technique) return null

  return (
    <div ref={detailRef} className="technique-detail" style={{ '--accent-color': technique.color }}>
      <div className="detail-header">
        <div className="detail-3d">
          <Canvas>
            <ambientLight intensity={0.5} />
            <pointLight position={[5, 5, 5]} intensity={1} color={technique.color} />
            <TechniqueModel color={technique.color} />
          </Canvas>
        </div>
        <div className="detail-info">
          <span className="detail-label" style={{ color: technique.color }}>
            {technique.icon} {technique.subtitle}
          </span>
          <h2 className="detail-title">{technique.title}</h2>
          <p className="detail-description">{technique.description}</p>
        </div>
      </div>

      <div className="detail-content">
        <div className="detail-section">
          <h4>Temel Özellikler</h4>
          <ul className="detail-list">
            {technique.details.map((detail, i) => (
              <li key={i}>
                <span className="list-marker" style={{ background: technique.color }}></span>
                {detail}
              </li>
            ))}
          </ul>
        </div>

        <div className="detail-section">
          <h4>Uygulama Alanları</h4>
          <div className="detail-tags">
            {technique.applications.map((app, i) => (
              <span key={i} className="detail-tag" style={{ borderColor: technique.color }}>
                {app}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const TechniquesSection = () => {
  const sectionRef = useRef()
  const [activeTechnique, setActiveTechnique] = useState(techniques[0].id)

  useEffect(() => {
    gsap.fromTo('.techniques-header',
      { y: 50, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 80%',
          toggleActions: 'play none none reverse'
        }
      }
    )
  }, [])

  const currentTechnique = techniques.find(t => t.id === activeTechnique)

  return (
    <section ref={sectionRef} id="techniques" className="techniques-section">
      <div className="grid-pattern"></div>

      <div className="container">
        <div className="techniques-header">
          <span className="section-label">Modern Sinirbilim Teknikleri</span>
          <h2 className="section-title">Nöral Devreleri Anlamak</h2>
          <p className="section-subtitle">
            Günümüz sinirbiliminin en güçlü araçlarını keşfedin. Her teknik,
            beyin işleyişini farklı bir perspektiften aydınlatır.
          </p>
        </div>

        <div className="techniques-content">
          <div className="techniques-grid">
            {techniques.map((technique, index) => (
              <TechniqueCard
                key={technique.id}
                technique={technique}
                index={index}
                isActive={activeTechnique === technique.id}
                onClick={setActiveTechnique}
              />
            ))}
          </div>

          <TechniqueDetail technique={currentTechnique} />
        </div>
      </div>

      <div className="section-glow glow-purple"></div>
    </section>
  )
}

export default TechniquesSection

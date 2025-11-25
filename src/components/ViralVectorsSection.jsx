import React, { useRef, useEffect, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial, Float } from '@react-three/drei'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import * as THREE from 'three'
import './ViralVectorsSection.css'

gsap.registerPlugin(ScrollTrigger)

function VirusParticle({ position, color, scale = 1 }) {
  const meshRef = useRef()
  const spikesRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.5
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.3
    }
  })

  const spikePositions = []
  for (let i = 0; i < 20; i++) {
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    spikePositions.push({
      position: [
        Math.sin(phi) * Math.cos(theta),
        Math.sin(phi) * Math.sin(theta),
        Math.cos(phi)
      ],
      rotation: [phi, theta, 0]
    })
  }

  return (
    <group position={position} scale={scale}>
      <Float speed={2} rotationIntensity={0.3}>
        <group ref={meshRef}>
          <Sphere args={[0.5, 32, 32]}>
            <MeshDistortMaterial
              color={color}
              transparent
              opacity={0.9}
              distort={0.2}
              speed={2}
              roughness={0.3}
              metalness={0.5}
            />
          </Sphere>
          {spikePositions.map((spike, i) => (
            <mesh key={i} position={spike.position.map(p => p * 0.55)} rotation={spike.rotation}>
              <coneGeometry args={[0.05, 0.15, 8]} />
              <meshStandardMaterial color={color} />
            </mesh>
          ))}
        </group>
      </Float>
    </group>
  )
}

function VirusScene({ color }) {
  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight position={[5, 5, 5]} intensity={1} color={color} />
      <pointLight position={[-5, -5, -5]} intensity={0.3} color="#ffffff" />
      <VirusParticle position={[0, 0, 0]} color={color} scale={1.5} />
    </>
  )
}

const viralVectors = [
  {
    id: 'aav',
    name: 'AAV',
    fullName: 'Adeno-Associated Virus',
    color: '#6366f1',
    description: 'Sinirbilimde en yaygın kullanılan viral vektör. Düşük immunojenisitesi ve uzun süreli gen ekspresyonu ile güvenli ve etkili.',
    serotypes: [
      { name: 'AAV1', target: 'Nöronlar (anterograde)' },
      { name: 'AAV2', target: 'Nöronlar (lokal)' },
      { name: 'AAV5', target: 'Geniş nöronal tropizm' },
      { name: 'AAV8', target: 'Periferik sinir sistemi' },
      { name: 'AAV9', target: 'Kan-beyin bariyerini geçer' },
      { name: 'AAVrg', target: 'Retrograde taşınım' }
    ],
    advantages: [
      'Düşük immunojenisite',
      'Uzun süreli ekspresyon',
      'Geniş serotip çeşitliliği',
      'Güvenli profil'
    ],
    applications: ['Gen terapisi', 'Optogenetik', 'Kemogenetik', 'Sensör ekspresyonu']
  },
  {
    id: 'rabies',
    name: 'Rabies',
    fullName: 'Modified Rabies Virus',
    color: '#ef4444',
    description: 'Monosinaptik retrograde tracing için altın standart. Tek sinaps geri giderek presinaptik partnerleri ortaya çıkarır.',
    serotypes: [
      { name: 'SAD-B19', target: 'Retrograde monosinaptik' },
      { name: 'CVS', target: 'Yüksek verimlilik' },
      { name: 'EnvA-pseudotyped', target: 'TVA-bağımlı giriş' }
    ],
    advantages: [
      'Monosinaptik spesifisite',
      'Yüksek etkinlik',
      'Presinaptik nöron haritalama',
      'TVA/G sistemi ile kontrol'
    ],
    applications: ['Devre haritalama', 'Input analizi', 'Konektom çalışmaları', 'Fonksiyonel bağlantı']
  },
  {
    id: 'prv',
    name: 'PRV',
    fullName: 'Pseudorabies Virus',
    color: '#22c55e',
    description: 'Polisinaptik retrograde tracer. Birden fazla sinaps geri giderek tüm upstream network\'ü ortaya çıkarır.',
    serotypes: [
      { name: 'PRV-Bartha', target: 'Attenuated strain' },
      { name: 'PRV-152', target: 'GFP ekspresyonu' },
      { name: 'PRV-614', target: 'RFP ekspresyonu' }
    ],
    advantages: [
      'Polisinaptik tracing',
      'Tüm network haritalama',
      'Temporal kontrol',
      'Dual-color tracing'
    ],
    applications: ['Otonom sinir sistemi', 'Motor devreler', 'Hipotalamik yolaklar', 'Viseral innervation']
  },
  {
    id: 'hsv',
    name: 'HSV',
    fullName: 'Herpes Simplex Virus',
    color: '#f59e0b',
    description: 'Büyük gen kapasitesi ile anterograde ve retrograde tracing. Yüksek payload kapasitesi ile kompleks genetik manipülasyonlar.',
    serotypes: [
      { name: 'HSV-1', target: 'Nörotropik' },
      { name: 'H129', target: 'Anterograde tracer' },
      { name: 'HSV amplicon', target: 'Büyük insert kapasitesi' }
    ],
    advantages: [
      'Büyük payload (~150kb)',
      'Anterograde tracing',
      'Hızlı ekspresyon',
      'Retrograde varyantlar'
    ],
    applications: ['Anterograde haritalama', 'Gen terapisi', 'Onkoloji', 'Büyük transgenlerin ekspresyonu']
  },
  {
    id: 'canine',
    name: 'CAV-2',
    fullName: 'Canine Adenovirus Type 2',
    color: '#ec4899',
    description: 'Retrograde taşınım için tercih edilen vektör. Nöronlarda yüksek tropizm ve düşük toksisite.',
    serotypes: [
      { name: 'CAV-2', target: 'Retrograde preferans' },
      { name: 'CAV-Cre', target: 'Cre-recombinase delivery' }
    ],
    advantages: [
      'Güçlü retrograde tropizm',
      'Düşük toksisite',
      'Stabil ekspresyon',
      'Cre-lox sistemi ile uyumlu'
    ],
    applications: ['Retrograde Cre delivery', 'Projeksiyon-spesifik manipülasyon', 'Devre-spesifik hedefleme', 'Intersectional genetik']
  }
]

const ViralVectorsSection = () => {
  const sectionRef = useRef()
  const [activeVirus, setActiveVirus] = useState(viralVectors[0])
  const [hoveredVirus, setHoveredVirus] = useState(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.viral-header',
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

      gsap.fromTo('.virus-card',
        { scale: 0.9, opacity: 0 },
        {
          scale: 1,
          opacity: 1,
          duration: 0.6,
          stagger: 0.1,
          ease: 'back.out(1.7)',
          scrollTrigger: {
            trigger: '.virus-grid',
            start: 'top 85%',
            toggleActions: 'play none none reverse'
          }
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} id="viral-vectors" className="viral-section">
      <div className="grid-pattern"></div>

      <div className="container">
        <div className="viral-header">
          <span className="section-label">Nöral Network Keşfi</span>
          <h2 className="section-title">Viral Vektörler</h2>
          <p className="section-subtitle">
            Nöral devrelerin haritalaması ve genetik manipülasyonu için kullanılan
            güçlü viral araçlar. Her vektör benzersiz özelliklere sahiptir.
          </p>
        </div>

        <div className="viral-content">
          <div className="virus-grid">
            {viralVectors.map((virus) => (
              <div
                key={virus.id}
                className={`virus-card ${activeVirus.id === virus.id ? 'active' : ''}`}
                onClick={() => setActiveVirus(virus)}
                onMouseEnter={() => setHoveredVirus(virus.id)}
                onMouseLeave={() => setHoveredVirus(null)}
                style={{ '--virus-color': virus.color }}
              >
                <div className="virus-3d">
                  <Canvas>
                    <VirusScene color={virus.color} />
                  </Canvas>
                </div>
                <div className="virus-info">
                  <h3>{virus.name}</h3>
                  <p>{virus.fullName}</p>
                </div>
                <div className="virus-indicator" style={{ background: virus.color }}></div>
              </div>
            ))}
          </div>

          <div className="virus-detail" style={{ '--virus-color': activeVirus.color }}>
            <div className="virus-detail-header">
              <div className="virus-detail-3d">
                <Canvas>
                  <VirusScene color={activeVirus.color} />
                </Canvas>
              </div>
              <div className="virus-detail-title">
                <span className="virus-badge" style={{ background: activeVirus.color }}>
                  {activeVirus.name}
                </span>
                <h2>{activeVirus.fullName}</h2>
                <p>{activeVirus.description}</p>
              </div>
            </div>

            <div className="virus-detail-content">
              <div className="virus-serotypes">
                <h4>Serotip & Hedef</h4>
                <div className="serotype-list">
                  {activeVirus.serotypes.map((serotype, i) => (
                    <div key={i} className="serotype-item">
                      <span className="serotype-name" style={{ color: activeVirus.color }}>
                        {serotype.name}
                      </span>
                      <span className="serotype-target">{serotype.target}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="virus-advantages">
                <h4>Avantajlar</h4>
                <ul>
                  {activeVirus.advantages.map((adv, i) => (
                    <li key={i}>
                      <span className="check-icon" style={{ color: activeVirus.color }}>✓</span>
                      {adv}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="virus-applications">
                <h4>Uygulama Alanları</h4>
                <div className="app-tags">
                  {activeVirus.applications.map((app, i) => (
                    <span key={i} className="app-tag" style={{ borderColor: activeVirus.color }}>
                      {app}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="viral-glow" style={{ background: activeVirus.color }}></div>
    </section>
  )
}

export default ViralVectorsSection

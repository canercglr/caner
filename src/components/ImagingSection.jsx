import React, { useRef, useEffect, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, MeshDistortMaterial, Sphere, OrbitControls } from '@react-three/drei'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import * as THREE from 'three'
import './ImagingSection.css'

gsap.registerPlugin(ScrollTrigger)

function BrainModel() {
  const brainRef = useRef()
  const regionsRef = useRef([])

  const regions = useMemo(() => [
    { pos: [0, 0.8, 0.3], size: 0.3, color: '#6366f1', name: 'Prefrontal Korteks' },
    { pos: [0.6, 0.3, 0.2], size: 0.25, color: '#22d3ee', name: 'Motor Korteks' },
    { pos: [-0.6, 0.3, 0.2], size: 0.25, color: '#22d3ee', name: 'Motor Korteks' },
    { pos: [0.8, -0.2, 0], size: 0.2, color: '#a855f7', name: 'Temporal Lob' },
    { pos: [-0.8, -0.2, 0], size: 0.2, color: '#a855f7', name: 'Temporal Lob' },
    { pos: [0, -0.3, -0.5], size: 0.35, color: '#10b981', name: 'Hipokampus' },
    { pos: [0, 0, 0.8], size: 0.2, color: '#ec4899', name: 'Amigdala' },
    { pos: [0, -0.8, -0.3], size: 0.4, color: '#f97316', name: 'Serebellum' },
  ], [])

  useFrame((state) => {
    if (brainRef.current) {
      brainRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.3
    }
    regionsRef.current.forEach((region, i) => {
      if (region) {
        const pulse = Math.sin(state.clock.elapsedTime * 2 + i) * 0.1 + 1
        region.scale.setScalar(pulse)
      }
    })
  })

  return (
    <group ref={brainRef}>
      {/* Main brain shape */}
      <Float speed={1.5} rotationIntensity={0.2}>
        <mesh scale={1.5}>
          <sphereGeometry args={[1, 64, 64]} />
          <MeshDistortMaterial
            color="#1a1a2e"
            transparent
            opacity={0.3}
            distort={0.3}
            speed={1}
            wireframe
          />
        </mesh>
      </Float>

      {/* Brain regions */}
      {regions.map((region, i) => (
        <Sphere
          key={i}
          ref={el => regionsRef.current[i] = el}
          args={[region.size, 32, 32]}
          position={region.pos}
        >
          <meshStandardMaterial
            color={region.color}
            transparent
            opacity={0.8}
            emissive={region.color}
            emissiveIntensity={0.3}
          />
        </Sphere>
      ))}

      {/* Synaptic connections */}
      {regions.slice(0, -1).map((region, i) => {
        const nextRegion = regions[i + 1]
        const points = [
          new THREE.Vector3(...region.pos),
          new THREE.Vector3(...nextRegion.pos)
        ]
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        return (
          <line key={i} geometry={geometry}>
            <lineBasicMaterial color="#6366f1" transparent opacity={0.3} />
          </line>
        )
      })}
    </group>
  )
}

const imagingTechniques = [
  {
    name: 'İki-Foton Mikroskopi',
    icon: '🔬',
    color: '#6366f1',
    description: 'Canlı dokuda derin görüntüleme. Nöronların aktivitesini gerçek zamanlı izleme.',
    features: [
      'Derin doku penetrasyonu (~1mm)',
      'Düşük fototoksisite',
      'In vivo kalsiyum görüntüleme',
      'Dendritic spine dinamikleri'
    ],
    applications: ['Kortikal aktivite', 'Sinaptik plastisite', 'Vasküler dinamikler']
  },
  {
    name: 'Light-Sheet Mikroskopi',
    icon: '💫',
    color: '#22d3ee',
    description: 'Tüm beynin hızlı 3D görüntülenmesi. Şeffaflaştırılmış dokularda yüksek çözünürlük.',
    features: [
      'Hızlı hacimsel görüntüleme',
      'Düşük foto-bleaching',
      'Tüm beyin haritalama',
      'Cleared tissue uyumu'
    ],
    applications: ['Konektom haritalama', 'Gelişim çalışmaları', 'Tümör görüntüleme']
  },
  {
    name: 'Tissue Clearing',
    icon: '🧊',
    color: '#a855f7',
    description: 'Dokuların optik olarak şeffaflaştırılması. Tüm organ görüntüleme için kritik.',
    features: [
      'CLARITY protokolü',
      'iDISCO metodları',
      'CUBIC yaklaşımı',
      '3D immunostaining'
    ],
    applications: ['Tüm beyin analizi', 'Vasküler haritalama', 'Nöronal popülasyonlar']
  },
  {
    name: 'fMRI',
    icon: '🧠',
    color: '#10b981',
    description: 'Fonksiyonel manyetik rezonans görüntüleme. Non-invaziv beyin aktivite haritalama.',
    features: [
      'BOLD sinyali',
      'Resting-state bağlantı',
      'Task-based aktivasyon',
      'Tüm beyin kapsam'
    ],
    applications: ['Bağlantı analizi', 'Network haritalama', 'Klinik çalışmalar']
  },
  {
    name: 'PET İmaging',
    icon: '☢️',
    color: '#f97316',
    description: 'Pozitron emisyon tomografisi. Moleküler hedeflerin in vivo görüntülenmesi.',
    features: [
      'Reseptör haritalama',
      'Metabolik aktivite',
      'Nörotransmitter salınımı',
      'Radyoligand kullanımı'
    ],
    applications: ['Dopamin sistemi', 'Nöroinflamasyon', 'Alzheimer biyobelirteçleri']
  },
  {
    name: 'Miniscope',
    icon: '📹',
    color: '#ec4899',
    description: 'Miniaturize florescent mikroskop. Serbest hareket eden hayvanlarda kalsiyum görüntüleme.',
    features: [
      'Tek nöron çözünürlüğü',
      'Serbest hareket kaydı',
      'Uzun süreli izleme',
      'Kablosuz varyantlar'
    ],
    applications: ['Hipokampal kodlama', 'Hafıza izleri', 'Sosyal davranış']
  }
]

const ImagingSection = () => {
  const sectionRef = useRef()

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.imaging-header',
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

      gsap.fromTo('.imaging-card',
        { y: 50, opacity: 0, rotateX: -10 },
        {
          y: 0,
          opacity: 1,
          rotateX: 0,
          duration: 0.6,
          stagger: 0.1,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: '.imaging-grid',
            start: 'top 85%',
            toggleActions: 'play none none reverse'
          }
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} id="imaging" className="imaging-section">
      <div className="grid-pattern"></div>

      <div className="container">
        <div className="imaging-header">
          <span className="section-label">Beyin Görüntüleme</span>
          <h2 className="section-title">Whole Brain Imaging</h2>
          <p className="section-subtitle">
            Modern görüntüleme teknikleri ile beynin yapısal ve fonksiyonel
            organizasyonunu hücresel çözünürlükte inceleyin.
          </p>
        </div>

        <div className="imaging-content">
          <div className="imaging-3d">
            <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
              <ambientLight intensity={0.3} />
              <pointLight position={[5, 5, 5]} intensity={1} color="#6366f1" />
              <pointLight position={[-5, -5, 5]} intensity={0.5} color="#ec4899" />
              <pointLight position={[0, -5, -5]} intensity={0.5} color="#22d3ee" />
              <BrainModel />
              <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
            </Canvas>
            <div className="brain-label">
              <span>İnteraktif 3D Beyin Modeli</span>
              <small>Sürükleyerek döndürün</small>
            </div>
          </div>

          <div className="imaging-grid">
            {imagingTechniques.map((tech, index) => (
              <div
                key={index}
                className="imaging-card"
                style={{ '--card-color': tech.color }}
              >
                <div className="imaging-card-header">
                  <span className="imaging-icon">{tech.icon}</span>
                  <h3>{tech.name}</h3>
                </div>
                <p className="imaging-description">{tech.description}</p>
                <div className="imaging-features">
                  {tech.features.map((feature, i) => (
                    <div key={i} className="feature-item">
                      <span className="feature-dot" style={{ background: tech.color }}></span>
                      {feature}
                    </div>
                  ))}
                </div>
                <div className="imaging-apps">
                  {tech.applications.map((app, i) => (
                    <span key={i} className="app-badge" style={{ borderColor: tech.color }}>
                      {app}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="imaging-glow-1"></div>
      <div className="imaging-glow-2"></div>
    </section>
  )
}

export default ImagingSection

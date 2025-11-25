import React, { useRef, useEffect, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, RoundedBox } from '@react-three/drei'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import * as THREE from 'three'
import './BehaviorSection.css'

gsap.registerPlugin(ScrollTrigger)

function MazeVisualization() {
  const groupRef = useRef()

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.3
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1
    }
  })

  const walls = [
    { pos: [0, 0.15, -2], size: [4, 0.3, 0.1] },
    { pos: [0, 0.15, 2], size: [4, 0.3, 0.1] },
    { pos: [-2, 0.15, 0], size: [0.1, 0.3, 4] },
    { pos: [2, 0.15, 0], size: [0.1, 0.3, 4] },
    { pos: [0, 0.15, 0], size: [2, 0.3, 0.1] },
    { pos: [-1, 0.15, 1], size: [0.1, 0.3, 2] },
    { pos: [1, 0.15, -1], size: [0.1, 0.3, 2] },
  ]

  return (
    <group ref={groupRef}>
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[4, 4]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>

      {/* Walls */}
      {walls.map((wall, i) => (
        <RoundedBox key={i} args={wall.size} position={wall.pos} radius={0.02}>
          <meshStandardMaterial color="#6366f1" transparent opacity={0.8} />
        </RoundedBox>
      ))}

      {/* Mouse indicator */}
      <Float speed={3} floatIntensity={0.2}>
        <mesh position={[-1.5, 0.2, -1.5]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={0.5} />
        </mesh>
      </Float>

      {/* Goal */}
      <mesh position={[1.5, 0.1, 1.5]}>
        <cylinderGeometry args={[0.2, 0.2, 0.05, 32]} />
        <meshStandardMaterial color="#10b981" emissive="#10b981" emissiveIntensity={0.5} />
      </mesh>
    </group>
  )
}

const behaviorTests = [
  {
    category: 'Öğrenme & Hafıza',
    color: '#6366f1',
    tests: [
      {
        name: 'Morris Water Maze',
        description: 'Uzaysal öğrenme ve hafıza testi. Gizli platformu bulmak için uzaysal ipuçları kullanılır.',
        measures: ['Kaçış latansı', 'Platform geçişleri', 'Kadran süresi']
      },
      {
        name: 'Novel Object Recognition',
        description: 'Nesne tanıma hafızası. Tanıdık ve yeni nesneler arasındaki tercih değerlendirilir.',
        measures: ['Tanıma indeksi', 'Eksplorasyon süresi', 'Diskriminasyon oranı']
      },
      {
        name: 'Barnes Maze',
        description: 'Su mazeden kaçınmak için kuru alternatif. Dairesel platformda kaçış deliği aranır.',
        measures: ['Kaçış latansı', 'Hata sayısı', 'Strateji analizi']
      },
      {
        name: 'Fear Conditioning',
        description: 'Bağlamsal ve ipucu-bağımlı korku hafızası testleri.',
        measures: ['Donma süresi', 'Şartlı yanıt', 'Söndürme']
      }
    ]
  },
  {
    category: 'Anksiyete & Depresyon',
    color: '#a855f7',
    tests: [
      {
        name: 'Elevated Plus Maze',
        description: 'Açık ve kapalı kollar arasındaki tercih ile anksiyete değerlendirmesi.',
        measures: ['Açık kol süresi', 'Giriş sayısı', 'Risk değerlendirme']
      },
      {
        name: 'Open Field Test',
        description: 'Genel lokomotor aktivite ve açık alan anksiyetesi.',
        measures: ['Toplam mesafe', 'Merkez süresi', 'Dikey aktivite']
      },
      {
        name: 'Forced Swim Test',
        description: 'Depresyon-benzeri davranış ölçümü. Hareketsizlik süresi değerlendirilir.',
        measures: ['Hareketsizlik', 'Yüzme', 'Tırmanma']
      },
      {
        name: 'Tail Suspension Test',
        description: 'Antidepresan etkinlik testi. Kuyruğundan asılan farede hareketsizlik.',
        measures: ['Hareketsizlik süresi', 'Aktif mücadele', 'Latans']
      }
    ]
  },
  {
    category: 'Sosyal Davranış',
    color: '#ec4899',
    tests: [
      {
        name: 'Three-Chamber Test',
        description: 'Sosyal tercih ve sosyal tanıma. Üç odacıklı aparatta yabancı fare tercihi.',
        measures: ['Sosyallik indeksi', 'Sosyal hafıza', 'Tercih oranı']
      },
      {
        name: 'Resident-Intruder',
        description: 'Agresyon ve sosyal dominans testi. Ev sahibi farenin tepkisi.',
        measures: ['Saldırı latansı', 'Saldırı süresi', 'Sosyal araştırma']
      },
      {
        name: 'Tube Dominance',
        description: 'Sosyal hiyerarşi belirleme. Dar tüpte karşılaşma sonucu.',
        measures: ['Kazanma oranı', 'Geri çekilme', 'Dominans sırası']
      }
    ]
  },
  {
    category: 'Motor Fonksiyon',
    color: '#10b981',
    tests: [
      {
        name: 'Rotarod',
        description: 'Motor koordinasyon ve denge. Dönen silindirde kalma süresi.',
        measures: ['Düşme latansı', 'RPM', 'Öğrenme eğrisi']
      },
      {
        name: 'Beam Walking',
        description: 'İnce koordinasyon ve denge. Dar çubuk üzerinde yürüme.',
        measures: ['Geçiş süresi', 'Ayak kayması', 'Düşme sayısı']
      },
      {
        name: 'Grip Strength',
        description: 'Kas gücü ölçümü. Kavrama kuvveti değerlendirmesi.',
        measures: ['Ön ayak gücü', 'Tüm ayak gücü', 'Yorulma']
      }
    ]
  }
]

const BehaviorSection = () => {
  const sectionRef = useRef()
  const [activeCategory, setActiveCategory] = useState(0)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.behavior-header',
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

      gsap.fromTo('.behavior-tab',
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: '.behavior-tabs',
            start: 'top 85%',
            toggleActions: 'play none none reverse'
          }
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} id="behavior" className="behavior-section">
      <div className="grid-pattern"></div>

      <div className="container">
        <div className="behavior-header">
          <span className="section-label">Davranışsal Nörobilim</span>
          <h2 className="section-title">Davranış Testleri</h2>
          <p className="section-subtitle">
            Fare ve sıçanlarda kullanılan standart davranış testleri.
            Bilişsel, duygusal ve motor fonksiyonların değerlendirilmesi.
          </p>
        </div>

        <div className="behavior-content">
          <div className="behavior-visual">
            <div className="maze-container">
              <Canvas camera={{ position: [4, 4, 4], fov: 50 }}>
                <ambientLight intensity={0.4} />
                <pointLight position={[5, 5, 5]} intensity={1} color="#6366f1" />
                <pointLight position={[-5, 5, -5]} intensity={0.5} color="#a855f7" />
                <MazeVisualization />
              </Canvas>
            </div>
            <div className="maze-label">
              <span>3D Maze Visualization</span>
            </div>
          </div>

          <div className="behavior-tests">
            <div className="behavior-tabs">
              {behaviorTests.map((category, index) => (
                <button
                  key={index}
                  className={`behavior-tab ${activeCategory === index ? 'active' : ''}`}
                  onClick={() => setActiveCategory(index)}
                  style={{ '--tab-color': category.color }}
                >
                  {category.category}
                </button>
              ))}
            </div>

            <div className="tests-grid">
              {behaviorTests[activeCategory].tests.map((test, index) => (
                <div
                  key={index}
                  className="test-card"
                  style={{ '--card-color': behaviorTests[activeCategory].color }}
                >
                  <h3>{test.name}</h3>
                  <p>{test.description}</p>
                  <div className="test-measures">
                    <span className="measures-label">Ölçümler:</span>
                    <div className="measures-list">
                      {test.measures.map((measure, i) => (
                        <span key={i} className="measure-tag">{measure}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="behavior-glow"></div>
    </section>
  )
}

export default BehaviorSection

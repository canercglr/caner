import React, { useRef, useEffect, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Line } from '@react-three/drei'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import * as THREE from 'three'
import './TracingSection.css'

gsap.registerPlugin(ScrollTrigger)

function NeuralPath({ start, end, color, speed = 1 }) {
  const lineRef = useRef()
  const progressRef = useRef(0)

  const curve = useMemo(() => {
    const mid = new THREE.Vector3().lerpVectors(
      new THREE.Vector3(...start),
      new THREE.Vector3(...end),
      0.5
    )
    mid.y += 0.5
    return new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(...start),
      mid,
      new THREE.Vector3(...end)
    )
  }, [start, end])

  const points = useMemo(() => curve.getPoints(50), [curve])

  useFrame((state) => {
    progressRef.current = (Math.sin(state.clock.elapsedTime * speed) + 1) / 2
  })

  return (
    <Line
      points={points}
      color={color}
      lineWidth={2}
      transparent
      opacity={0.6}
    />
  )
}

function TracingVisualization() {
  const groupRef = useRef()
  const neurons = useMemo(() => {
    const nodes = []
    const gridSize = 3
    for (let x = -gridSize; x <= gridSize; x += 1.5) {
      for (let z = -gridSize; z <= gridSize; z += 1.5) {
        nodes.push({
          position: [x + (Math.random() - 0.5) * 0.5, (Math.random() - 0.5) * 2, z + (Math.random() - 0.5) * 0.5],
          color: new THREE.Color().setHSL(0.6 + Math.random() * 0.4, 0.8, 0.6)
        })
      }
    }
    return nodes
  }, [])

  const connections = useMemo(() => {
    const paths = []
    const colors = ['#6366f1', '#22d3ee', '#a855f7', '#10b981', '#f97316']
    neurons.forEach((n1, i) => {
      const nearby = neurons.filter((n2, j) => {
        if (i === j) return false
        const dist = Math.sqrt(
          Math.pow(n1.position[0] - n2.position[0], 2) +
          Math.pow(n1.position[1] - n2.position[1], 2) +
          Math.pow(n1.position[2] - n2.position[2], 2)
        )
        return dist < 2.5
      })
      nearby.slice(0, 2).forEach(n2 => {
        paths.push({
          start: n1.position,
          end: n2.position,
          color: colors[Math.floor(Math.random() * colors.length)]
        })
      })
    })
    return paths
  }, [neurons])

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1
    }
  })

  return (
    <group ref={groupRef}>
      {neurons.map((neuron, i) => (
        <Float key={i} speed={2} floatIntensity={0.2}>
          <mesh position={neuron.position}>
            <sphereGeometry args={[0.1, 16, 16]} />
            <meshStandardMaterial
              color={neuron.color}
              emissive={neuron.color}
              emissiveIntensity={0.5}
            />
          </mesh>
        </Float>
      ))}
      {connections.map((conn, i) => (
        <NeuralPath
          key={i}
          start={conn.start}
          end={conn.end}
          color={conn.color}
          speed={0.5 + Math.random()}
        />
      ))}
    </group>
  )
}

const tracingMethods = [
  {
    title: 'Anterograde Tracing',
    icon: '➡️',
    description: 'Nöronların aksonları boyunca ilerleyerek projeksiyon hedeflerini ortaya çıkarır.',
    methods: ['BDA', 'PHA-L', 'AAV', 'HSV-H129'],
    color: '#6366f1'
  },
  {
    title: 'Retrograde Tracing',
    icon: '⬅️',
    description: 'Akson terminallerinden hücre gövdesine geri giderek input kaynaklarını belirler.',
    methods: ['CTB', 'Fluorogold', 'Retrobeads', 'Rabies'],
    color: '#22d3ee'
  },
  {
    title: 'Transsinaptik Tracing',
    icon: '🔄',
    description: 'Sinapslar arasında geçerek bağlı nöral devrelerin tamamını haritalama.',
    methods: ['Modified Rabies', 'PRV', 'HSV', 'WGA'],
    color: '#a855f7'
  },
  {
    title: 'Kombinatoryal Yaklaşımlar',
    icon: '🧩',
    description: 'Birden fazla yöntemi birleştirerek devre spesifik manipülasyon ve haritalama.',
    methods: ['TRIO', 'cTRIO', 'Dual-virus', 'Intersectional'],
    color: '#10b981'
  }
]

const TracingSection = () => {
  const sectionRef = useRef()
  const cardsRef = useRef([])

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.tracing-header',
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

      gsap.fromTo('.tracing-method-card',
        { x: -50, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.6,
          stagger: 0.15,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: '.tracing-methods',
            start: 'top 85%',
            toggleActions: 'play none none reverse'
          }
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} id="tracing" className="tracing-section">
      <div className="grid-pattern"></div>

      <div className="container">
        <div className="tracing-layout">
          <div className="tracing-left">
            <div className="tracing-header">
              <span className="section-label">Devre Keşfi</span>
              <h2 className="section-title">Neural Tracing</h2>
              <p className="section-subtitle">
                Beyin devrelerinin anatomik haritalaması için kullanılan tracing
                teknikleri. Nöronların bağlantılarını izleyerek devreleri ortaya çıkarır.
              </p>
            </div>

            <div className="tracing-methods">
              {tracingMethods.map((method, index) => (
                <div
                  key={index}
                  className="tracing-method-card"
                  style={{ '--method-color': method.color }}
                >
                  <div className="method-icon">{method.icon}</div>
                  <div className="method-content">
                    <h3>{method.title}</h3>
                    <p>{method.description}</p>
                    <div className="method-tags">
                      {method.methods.map((m, i) => (
                        <span key={i} className="method-tag">{m}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="tracing-visualization">
            <div className="visualization-container">
              <Canvas camera={{ position: [0, 2, 8], fov: 50 }}>
                <ambientLight intensity={0.3} />
                <pointLight position={[5, 5, 5]} intensity={1} color="#6366f1" />
                <pointLight position={[-5, -5, -5]} intensity={0.5} color="#a855f7" />
                <TracingVisualization />
              </Canvas>
              <div className="visualization-overlay">
                <span>İnteraktif Neural Network Görselleştirmesi</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="tracing-glow"></div>
    </section>
  )
}

export default TracingSection

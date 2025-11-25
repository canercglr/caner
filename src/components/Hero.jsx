import React, { useRef, useEffect, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Float, Sparkles, MeshDistortMaterial } from '@react-three/drei'
import { gsap } from 'gsap'
import * as THREE from 'three'
import './Hero.css'

function NeuronNetwork() {
  const groupRef = useRef()
  const particlesRef = useRef()

  const neurons = useMemo(() => {
    const points = []
    const count = 50
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const radius = 2.5 + Math.random() * 1.5
      points.push({
        position: new THREE.Vector3(
          radius * Math.sin(phi) * Math.cos(theta),
          radius * Math.sin(phi) * Math.sin(theta),
          radius * Math.cos(phi)
        ),
        color: new THREE.Color().setHSL(0.7 + Math.random() * 0.3, 0.8, 0.6)
      })
    }
    return points
  }, [])

  const connections = useMemo(() => {
    const lines = []
    neurons.forEach((neuron, i) => {
      const nearby = neurons.filter((n, j) =>
        j !== i && neuron.position.distanceTo(n.position) < 2
      ).slice(0, 3)
      nearby.forEach(n => {
        lines.push({ start: neuron.position, end: n.position })
      })
    })
    return lines
  }, [neurons])

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1
    }
  })

  return (
    <group ref={groupRef}>
      {/* Central Brain Mesh */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <mesh scale={1.8}>
          <icosahedronGeometry args={[1, 4]} />
          <MeshDistortMaterial
            color="#6366f1"
            transparent
            opacity={0.3}
            distort={0.4}
            speed={2}
            wireframe
          />
        </mesh>
      </Float>

      {/* Neurons */}
      {neurons.map((neuron, i) => (
        <mesh key={i} position={neuron.position}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshBasicMaterial color={neuron.color} />
        </mesh>
      ))}

      {/* Neural Connections */}
      {connections.map((conn, i) => {
        const points = [conn.start, conn.end]
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        return (
          <line key={i} geometry={geometry}>
            <lineBasicMaterial color="#22d3ee" transparent opacity={0.3} />
          </line>
        )
      })}

      {/* Sparkles */}
      <Sparkles
        count={200}
        scale={8}
        size={1.5}
        speed={0.5}
        opacity={0.5}
        color="#a855f7"
      />
    </group>
  )
}

function FloatingParticles() {
  const particlesRef = useRef()
  const count = 500

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20
      pos[i * 3 + 1] = (Math.random() - 0.5) * 20
      pos[i * 3 + 2] = (Math.random() - 0.5) * 20
    }
    return pos
  }, [])

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.elapsedTime * 0.02
    }
  })

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#6366f1"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  )
}

function Scene() {
  const { camera } = useThree()

  useEffect(() => {
    camera.position.z = 6
  }, [camera])

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#6366f1" />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ec4899" />
      <NeuronNetwork />
      <FloatingParticles />
    </>
  )
}

const Hero = () => {
  const heroRef = useRef()
  const textRef = useRef()

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo('.hero-title-line',
        { y: 100, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, stagger: 0.2, delay: 2.2, ease: 'power3.out' }
      )

      gsap.fromTo('.hero-description',
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, delay: 2.8, ease: 'power2.out' }
      )

      gsap.fromTo('.hero-cta',
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, delay: 3, ease: 'power2.out' }
      )

      gsap.fromTo('.hero-stats',
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, delay: 3.2, ease: 'power2.out' }
      )
    }, heroRef)

    return () => ctx.revert()
  }, [])

  const scrollToSection = (id) => {
    document.querySelector(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section ref={heroRef} className="hero">
      <div className="hero-canvas">
        <Canvas dpr={[1, 2]} camera={{ fov: 45 }}>
          <Scene />
        </Canvas>
      </div>

      <div className="hero-content">
        <div className="hero-text" ref={textRef}>
          <h1 className="hero-title">
            <span className="hero-title-line">Sinirbilimin</span>
            <span className="hero-title-line gradient">Geleceğini</span>
            <span className="hero-title-line">Keşfedin</span>
          </h1>

          <p className="hero-description">
            Türkiye'nin en kapsamlı nörobilim teknikler rehberi. Optogenetik'ten
            kemogenetik'e, fiber fotometriden viral tracing'e kadar modern
            sinirbilim metodlarını interaktif olarak öğrenin.
          </p>

          <div className="hero-cta">
            <button
              className="btn-primary"
              onClick={() => scrollToSection('#techniques')}
            >
              <span>Keşfetmeye Başla</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </button>
            <button className="btn-secondary">
              <span>Teknikler Hakkında</span>
            </button>
          </div>
        </div>

        <div className="hero-stats">
          <div className="stat">
            <span className="stat-number">10+</span>
            <span className="stat-label">Modern Teknik</span>
          </div>
          <div className="stat">
            <span className="stat-number">5+</span>
            <span className="stat-label">Viral Vektör</span>
          </div>
          <div className="stat">
            <span className="stat-number">100%</span>
            <span className="stat-label">Türkçe İçerik</span>
          </div>
        </div>
      </div>

      <div className="hero-scroll">
        <div className="scroll-indicator">
          <span>Aşağı Kaydır</span>
          <div className="scroll-line">
            <div className="scroll-dot"></div>
          </div>
        </div>
      </div>

      <div className="hero-glow glow-1"></div>
      <div className="hero-glow glow-2"></div>
      <div className="hero-glow glow-3"></div>
    </section>
  )
}

export default Hero

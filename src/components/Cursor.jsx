import React, { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import './Cursor.css'

const Cursor = () => {
  const cursorRef = useRef(null)
  const cursorDotRef = useRef(null)

  useEffect(() => {
    const cursor = cursorRef.current
    const cursorDot = cursorDotRef.current

    const moveCursor = (e) => {
      gsap.to(cursor, {
        x: e.clientX,
        y: e.clientY,
        duration: 0.5,
        ease: 'power2.out'
      })
      gsap.to(cursorDot, {
        x: e.clientX,
        y: e.clientY,
        duration: 0.1
      })
    }

    const handleHover = () => {
      gsap.to(cursor, {
        scale: 2,
        opacity: 0.5,
        duration: 0.3
      })
    }

    const handleHoverEnd = () => {
      gsap.to(cursor, {
        scale: 1,
        opacity: 1,
        duration: 0.3
      })
    }

    window.addEventListener('mousemove', moveCursor)

    const hoverElements = document.querySelectorAll('a, button, .hover-target')
    hoverElements.forEach(el => {
      el.addEventListener('mouseenter', handleHover)
      el.addEventListener('mouseleave', handleHoverEnd)
    })

    return () => {
      window.removeEventListener('mousemove', moveCursor)
      hoverElements.forEach(el => {
        el.removeEventListener('mouseenter', handleHover)
        el.removeEventListener('mouseleave', handleHoverEnd)
      })
    }
  }, [])

  return (
    <>
      <div ref={cursorRef} className="cursor" />
      <div ref={cursorDotRef} className="cursor-dot" />
    </>
  )
}

export default Cursor

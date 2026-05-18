'use client'

import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text } from '@react-three/drei'
import * as THREE from 'three'

function BrainRegion({ position, activation, label, color }: {
  position: [number, number, number]
  activation: number
  label: string
  color: string
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1
    }
    if (glowRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.05 * activation
      glowRef.current.scale.setScalar(scale)
    }
  })
  
  const intensity = Math.max(0, Math.min(1, activation))
  const radius = 0.3 + intensity * 0.4
  
  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[radius, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={intensity * 0.8}
          transparent
          opacity={0.6 + intensity * 0.4}
        />
      </mesh>
      <mesh ref={glowRef}>
        <sphereGeometry args={[radius * 1.3, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={intensity * 0.3}
          transparent
          opacity={0.15}
        />
      </mesh>
      <Text
        position={[0, radius + 0.3, 0]}
        fontSize={0.15}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
      <Text
        position={[0, radius + 0.15, 0]}
        fontSize={0.1}
        color={intensity > 0.7 ? '#4deeea' : '#888888'}
        anchorX="center"
        anchorY="middle"
      >
        {(intensity * 100).toFixed(0)}%
      </Text>
    </group>
  )
}

function BrainWireframe() {
  return (
    <mesh>
      <sphereGeometry args={[2.2, 32, 32]} />
      <meshStandardMaterial
        color="#333344"
        wireframe
        transparent
        opacity={0.15}
      />
    </mesh>
  )
}

function BrainConnections({ regions }: { regions: Array<{ position: [number, number, number]; activation: number }> }) {
  const lineMaterial = useMemo(() => new THREE.LineBasicMaterial({
    color: '#4deeea',
    transparent: true,
    opacity: 0.2,
  }), [])
  
  const points = regions.flatMap((r, i) =>
    regions.slice(i + 1).map((r2) => {
      if (r.activation > 0.4 && r2.activation > 0.4) {
        return [r.position, r2.position]
      }
      return null
    }).filter(Boolean)
  ).flat()
  
  if (points.length === 0) return null
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    const positions = new Float32Array(points.length * 3)
    points.forEach((p, i) => {
      positions[i * 3] = p[0]
      positions[i * 3 + 1] = p[1]
      positions[i * 3 + 2] = p[2]
    })
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    return geo
  }, [points])
  
  return <lineSegments geometry={geometry} material={lineMaterial} />
}

export default function Brain3D({ brainData }: {
  brainData?: {
    cortical_response?: {
      visual_cortex?: number
      auditory_cortex?: number
      language_center?: number
      amygdala?: number
      prefrontal_cortex?: number
      reward_center?: number
      social_cognition?: number
      memory_formation?: number
    }
  }
}) {
  const cortical = brainData?.cortical_response || {}
  
  const regions = [
    { position: [0.8, 0.5, 0.8] as [number, number, number], activation: (cortical.visual_cortex || 0) / 100, label: 'Visual', color: '#4deeea' },
    { position: [-0.8, 0.5, 0.8] as [number, number, number], activation: (cortical.auditory_cortex || 0) / 100, label: 'Auditory', color: '#a78bfa' },
    { position: [0, 1.2, 0.5] as [number, number, number], activation: (cortical.language_center || 0) / 100, label: 'Language', color: '#f59e0b' },
    { position: [0.6, -0.3, 0.6] as [number, number, number], activation: (cortical.amygdala || 0) / 100, label: 'Amygdala', color: '#ef4444' },
    { position: [0, 1.5, -0.3] as [number, number, number], activation: (cortical.prefrontal_cortex || 0) / 100, label: 'PFC', color: '#10b981' },
    { position: [0, 0.2, 0] as [number, number, number], activation: (cortical.reward_center || 0) / 100, label: 'Reward', color: '#f97316' },
    { position: [-0.6, 0.8, -0.5] as [number, number, number], activation: (cortical.social_cognition || 0) / 100, label: 'Social', color: '#ec4899' },
    { position: [0.5, 0, -0.8] as [number, number, number], activation: (cortical.memory_formation || 0) / 100, label: 'Memory', color: '#06b6d4' },
  ]
  
  return (
    <div className="w-full h-[300px] glass-panel p-2">
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.5} />
        <pointLight position={[-10, -10, -10]} intensity={0.3} color="#4deeea" />
        
        <BrainWireframe />
        
        {regions.map((region, i) => (
          <BrainRegion key={i} {...region} />
        ))}
        
        <BrainConnections regions={regions} />
        
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.5}
          maxPolarAngle={Math.PI / 1.5}
          minPolarAngle={Math.PI / 3}
        />
      </Canvas>
    </div>
  )
}

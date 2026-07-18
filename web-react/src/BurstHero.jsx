import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  return reduced;
}

function DemandClock({ active }) {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    invalidate();
    if (!active) return undefined;
    const timer = window.setInterval(invalidate, 1000 / 24);
    return () => window.clearInterval(timer);
  }, [active, invalidate]);

  return null;
}

function EnergyRays() {
  const positions = useMemo(() => {
    const rays = new Float32Array(72 * 6);
    for (let index = 0; index < 72; index += 1) {
      const phase = index * 2.399963;
      const z = 1 - (2 * (index + 0.5)) / 72;
      const radial = Math.sqrt(1 - z * z);
      const length = 1.8 + (index % 9) * 0.22;
      rays[index * 6] = 0;
      rays[index * 6 + 1] = 0;
      rays[index * 6 + 2] = 0;
      rays[index * 6 + 3] = Math.cos(phase) * radial * length;
      rays[index * 6 + 4] = z * length;
      rays[index * 6 + 5] = Math.sin(phase) * radial * length;
    }
    return rays;
  }, []);

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial color="#d846ff" transparent opacity={0.26} />
    </lineSegments>
  );
}

function BurstModel({ animate }) {
  const burst = useRef(null);
  const core = useRef(null);
  const shell = useRef(null);

  useFrame(({ clock }) => {
    if (!animate) return;
    const elapsed = clock.getElapsedTime();
    if (burst.current) burst.current.rotation.y = elapsed * 0.13;
    if (core.current) {
      const pulse = 1 + Math.sin(elapsed * 2.3) * 0.09;
      core.current.scale.setScalar(pulse);
    }
    if (shell.current) {
      const expansion = 1 + ((elapsed * 0.14) % 0.32);
      shell.current.scale.setScalar(expansion);
      shell.current.material.opacity = 0.24 - (expansion - 1) * 0.45;
    }
  });

  return (
    <group ref={burst} rotation={[0.16, -0.2, 0.08]}>
      <mesh ref={core}>
        <icosahedronGeometry args={[0.55, 3]} />
        <meshStandardMaterial color="#ff57b0" emissive="#ee167e" emissiveIntensity={4.2} roughness={0.28} />
      </mesh>
      <mesh ref={shell}>
        <icosahedronGeometry args={[1.08, 2]} />
        <meshBasicMaterial color="#b34cff" wireframe transparent opacity={0.22} />
      </mesh>
      <mesh rotation={[0, 0, -Math.PI / 2]} position={[1.45, 0, 0]}>
        <coneGeometry args={[0.72, 2.7, 32, 1, true]} />
        <meshBasicMaterial color="#ff2f91" transparent opacity={0.2} side={2} depthWrite={false} />
      </mesh>
      <mesh rotation={[0, 0, Math.PI / 2]} position={[-1.45, 0, 0]}>
        <coneGeometry args={[0.72, 2.7, 32, 1, true]} />
        <meshBasicMaterial color="#8a5cff" transparent opacity={0.2} side={2} depthWrite={false} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.45, 0.025, 8, 64]} />
        <meshBasicMaterial color="#ff4ca6" transparent opacity={0.7} />
      </mesh>
      <mesh rotation={[Math.PI / 2.8, 0.4, 0]}>
        <torusGeometry args={[2.05, 0.018, 8, 64]} />
        <meshBasicMaterial color="#8f65ff" transparent opacity={0.45} />
      </mesh>
      <EnergyRays />
    </group>
  );
}

function StarPoints() {
  const positions = useMemo(() => {
    const points = new Float32Array(130 * 3);
    for (let index = 0; index < 130; index += 1) {
      const phase = index * 2.399963;
      const radius = 5.5 + (index % 13) * 0.28;
      points[index * 3] = Math.cos(phase) * radius;
      points[index * 3 + 1] = ((index * 31) % 79) / 8 - 4.8;
      points[index * 3 + 2] = Math.sin(phase) * radius - 1.5;
    }
    return points;
  }, []);
  return (
    <points>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry>
      <pointsMaterial color="#ffd7ed" size={0.035} transparent opacity={0.65} sizeAttenuation />
    </points>
  );
}

export default function BurstHero() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="burst-canvas" role="img" aria-label="Procedural radiating gamma-ray burst schematic">
      <Canvas
        camera={{ position: [4.7, 2.7, 5.4], fov: 39 }}
        dpr={[1, 1.35]}
        frameloop="demand"
        gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }}
      >
        <ambientLight intensity={0.75} />
        <pointLight position={[2, 3, 3]} intensity={32} color="#ff3d9d" />
        <pointLight position={[-3, -1, 2]} intensity={22} color="#8158ff" />
        <StarPoints />
        <BurstModel animate={!reducedMotion} />
        <DemandClock active={!reducedMotion} />
      </Canvas>
    </div>
  );
}

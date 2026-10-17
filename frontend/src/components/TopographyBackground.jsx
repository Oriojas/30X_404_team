import React from 'react'

export default function TopographyBackground() {
  // Generación de 36 curvas de nivel densas y cercanas (separación de ~32px)
  const diagonalWaves = Array.from({ length: 38 }, (_, i) => {
    const y = -80 + i * 32
    const curveOffset1 = Math.sin(i * 0.35) * 45
    const curveOffset2 = Math.cos(i * 0.35) * 35
    const isMaster = i % 5 === 0

    return {
      d: `M-100 ${y} C 320 ${y + 55 + curveOffset1}, 720 ${y - 45 - curveOffset2}, 1120 ${y + 50 + curveOffset1} C 1520 ${y - 35 + curveOffset2}, 1760 ${y + 40}, 2050 ${y + 10}`,
      isMaster,
      elevation: 60 + i * 10
    }
  })

  // Anillos concéntricos cercanos en la cresta superior derecha (paso de 18px)
  const ridgeRings = Array.from({ length: 20 }, (_, i) => ({
    rx: 25 + i * 18,
    ry: 14 + i * 10,
    cx: 1520,
    cy: 210,
    rot: -12,
    isMaster: i % 5 === 0,
    elevation: 100 + i * 10
  }))

  // Anillos concéntricos cercanos en la formación inferior izquierda (paso de 18px)
  const valleyRings = Array.from({ length: 16 }, (_, i) => ({
    rx: 20 + i * 18,
    ry: 12 + i * 10,
    cx: 300,
    cy: 760,
    rot: 10,
    isMaster: i % 5 === 0,
    elevation: 80 + i * 10
  }))

  return (
    <div
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none"
      aria-hidden="true"
    >
      <svg
        className="w-full h-full object-cover"
        viewBox="0 0 1920 1080"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        {/* Curvas de Nivel Ondulantes Trazadas Estrechamente */}
        {diagonalWaves.map((wave, idx) => (
          <path
            key={`wave-${idx}`}
            d={wave.d}
            stroke="#94A3B8"
            strokeWidth={wave.isMaster ? '1.0' : '0.65'}
            strokeOpacity={wave.isMaster ? '0.28' : '0.18'}
            fill="none"
          />
        ))}

        {/* Anillos Concéntricos Superiores (Cresta Noreste) */}
        {ridgeRings.map((ring, idx) => (
          <ellipse
            key={`ridge-${idx}`}
            cx={ring.cx}
            cy={ring.cy}
            rx={ring.rx}
            ry={ring.ry}
            transform={`rotate(${ring.rot} ${ring.cx} ${ring.cy})`}
            stroke="#94A3B8"
            strokeWidth={ring.isMaster ? '1.0' : '0.65'}
            strokeOpacity={ring.isMaster ? '0.28' : '0.18'}
            fill="none"
          />
        ))}

        {/* Anillos Concéntricos Inferiores (Formación Suroeste) */}
        {valleyRings.map((ring, idx) => (
          <ellipse
            key={`valley-${idx}`}
            cx={ring.cx}
            cy={ring.cy}
            rx={ring.rx}
            ry={ring.ry}
            transform={`rotate(${ring.rot} ${ring.cx} ${ring.cy})`}
            stroke="#94A3B8"
            strokeWidth={ring.isMaster ? '1.0' : '0.65'}
            strokeOpacity={ring.isMaster ? '0.28' : '0.18'}
            fill="none"
          />
        ))}

        {/* Micro-cotas de altitud discretas y tenues */}
        <g fill="#94A3B8" fillOpacity="0.25" className="font-mono text-[9px]">
          <text x="1560" y="210">100m</text>
          <text x="1650" y="210">150m</text>
          <text x="1740" y="210">200m</text>
          <text x="1830" y="210">250m</text>

          <text x="330" y="760">80m</text>
          <text x="420" y="760">130m</text>
          <text x="510" y="760">180m</text>

          <text x="750" y="380">120m</text>
          <text x="750" y="540">140m</text>
          <text x="750" y="700">160m</text>
        </g>
      </svg>
    </div>
  )
}

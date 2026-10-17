// Infraestructura de Blinka PayAgent en Railway (Fase 4).
// Reemplaza a Config as Code (railway.json), deprecado desde el 28-ago-2026.
// Los secretos nunca van aquí: se declaran con preserve() y se cargan en Railway.
import { defineRailway, github, postgres, preserve, project, service } from "railway/iac";

const REPO = "Oriojas/30X_404_team";
const BRANCH = "master";

export default defineRailway(() => {
  const db = postgres("Postgres");

  const backend = service("backend", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "/backend" }),
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["/backend/**"] },
    deploy: {
      healthcheckPath: "/api/health",
      healthcheckTimeout: 120,
      restartPolicyMaxRetries: 5, // ON_FAILURE es el default de Railway; declararlo deja drift permanente
    },
    env: {
      DATABASE_URL: db.env.DATABASE_URL,
      DB_AUTO_MIGRATE: "true",
      DB_SEED_DEMO: "true",
      ENVIRONMENT: "production",
      LOG_LEVEL: "info",
      GEMINI_MODEL: "gemini-3.8-flash",
      // Solo el dominio del frontend; nunca "*" en producción.
      ALLOWED_ORIGINS: "https://${{30X_404_team.RAILWAY_PUBLIC_DOMAIN}}",
      TELEGRAM_WEBHOOK_URL: "https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/webhook/telegram",
      GEMINI_API_KEY: preserve(),
      TELEGRAM_BOT_TOKEN: preserve(),
      TELEGRAM_WEBHOOK_SECRET: preserve(),
    },
  });

  // Servicio existente (dominio 30x404team-production.up.railway.app): se conserva su nombre
  // para que Railway no lo borre y lo vuelva a crear.
  const frontend = service("30X_404_team", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "/frontend" }),
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile", watchPatterns: ["/frontend/**"] },
    deploy: {
      healthcheckPath: "/",
      healthcheckTimeout: 60,
      restartPolicyMaxRetries: 5, // ON_FAILURE es el default de Railway; declararlo deja drift permanente
    },
    env: {
      // Vite la lee en el build (ARG en frontend/Dockerfile); cambiarla exige redeploy.
      VITE_API_BASE_URL: "https://${{backend.RAILWAY_PUBLIC_DOMAIN}}",
    },
  });

  return project("30x404team", {
    resources: [db, backend, frontend],
  });
});

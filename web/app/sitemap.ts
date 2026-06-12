import type { MetadataRoute } from "next";

// Páginas estáticas da aplicação. Produto por município não é enumerado aqui
// — o volume (~5.500 × 12 produtos) requer um sitemap particionado no futuro.
export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.PUBLIC_URL ?? "https://dadosabedoria.gov.br";
  const now = new Date();

  const estaticas: MetadataRoute.Sitemap = [
    { url: `${base}/`, lastModified: now, changeFrequency: "weekly", priority: 1.0 },
    { url: `${base}/ivm`, lastModified: now, changeFrequency: "monthly", priority: 0.9 },
    { url: `${base}/onde-foi`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${base}/comparar`, lastModified: now, changeFrequency: "weekly", priority: 0.7 },
    { url: `${base}/perguntar`, lastModified: now, changeFrequency: "weekly", priority: 0.7 },
    { url: `${base}/fontes`, lastModified: now, changeFrequency: "monthly", priority: 0.6 },
  ];

  return estaticas;
}

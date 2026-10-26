/**
 * @file theme.ts
 * @author naflashDev
 * @brief Contexto y tipos del Sistema de Diseño y Personalización Visual.
 * @details Implementa la selección interactiva de paletas, tipografías y modo oscuro/claro conforme a la Guía de Diseño Transversal de naflashDev.
 */

export type ThemePalette =
  | 'cyber-neon'
  | 'jetbrains-dark'
  | 'amber-terminal'
  | 'modern-saas'
  | 'calma-organica'
  | 'minimal-swiss';

export type FontFamily =
  | 'plus-jakarta'
  | 'geist'
  | 'inter'
  | 'space-grotesk'
  | 'jetbrains-mono';

export type ThemeMode = 'dark' | 'light';

export interface ThemeSettings {
  palette: ThemePalette;
  font: FontFamily;
  mode: ThemeMode;
}

export const PALETTES: { id: ThemePalette; name: string; primary: string; desc: string }[] = [
  { id: 'cyber-neon', name: 'Cyber Neon', primary: '#06b6d4', desc: 'Técnico, ciberseguridad, cyan neón sobre fondo zinc profundo' },
  { id: 'jetbrains-dark', name: 'JetBrains Dark', primary: '#f97316', desc: 'Ingeniería de software, naranja JetBrains sobre obsidian' },
  { id: 'amber-terminal', name: 'Amber Terminal', primary: '#f59e0b', desc: 'Retro terminal Unix, ámbar fósforo sobre negro OLED' },
  { id: 'modern-saas', name: 'Modern SaaS', primary: '#4f46e5', desc: 'Productividad, índigo y violeta en superficies slate' },
  { id: 'calma-organica', name: 'Calma Orgánica', primary: '#0f766e', desc: 'Anti-fatiga visual, verde petróleo y ámbar cálido' },
  { id: 'minimal-swiss', name: 'Minimal Swiss', primary: '#2563eb', desc: 'Rigor suizo, cobalto y escala de grises pura' },
];

export const FONTS: { id: FontFamily; name: string; category: string }[] = [
  { id: 'plus-jakarta', name: 'Plus Jakarta Sans', category: 'Geométrica & Moderna (Recomendada)' },
  { id: 'geist', name: 'Geist', category: 'Silicon Valley Vanguardista' },
  { id: 'inter', name: 'Inter', category: 'Ergonomía de Datos y Neutralidad' },
  { id: 'space-grotesk', name: 'Space Grotesk', category: 'Carácter Editorial Técnico' },
  { id: 'jetbrains-mono', name: 'JetBrains Mono', category: 'Código, Hashes y Consola' },
];

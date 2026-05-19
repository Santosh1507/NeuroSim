/**
 * Framer Motion easing constants.
 *
 * These are the definitive easing tokens from DESIGN.md / globals.css.
 * Every Framer Motion transition across the app should reference these
 * constants instead of inline cubic-bezier values or string aliases.
 *
 * CSS reference:
 *   --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
 *   --ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1);
 *   --ease-smooth:   cubic-bezier(0.4, 0, 0.2, 1);
 */

/** Dramatic deceleration — for hero reveals, modals, large layout shifts. */
export const easeOutExpo: [number, number, number, number] = [0.16, 1, 0.3, 1];

/** Overshoot spring — for micro-interactions, buttons, toggles. */
export const easeSpring: [number, number, number, number] = [0.34, 1.56, 0.64, 1];

/** Standard smooth — for panels, cards, tabs, most UI transitions. */
export const easeSmooth: [number, number, number, number] = [0.4, 0, 0.2, 1];

/** Quick micro-interaction (80ms). */
export const micro = { duration: 0.08, ease: easeOutExpo };

/** Standard fade-in with slight vertical offset. */
export const fadeIn = { duration: 0.5, ease: easeOutExpo };

/** Staggered entry for lists / grids. Factory: stagger(delayBase). */
export const staggerItem = (i: number, baseDelay = 0.06) => ({
  duration: 0.4,
  delay: i * baseDelay,
  ease: easeOutExpo,
});

/** Hero section reveal. Longer duration, larger offset. */
export const heroReveal = { duration: 0.7, ease: easeOutExpo };

/** Hero reveal with delay (secondary element). */
export const heroRevealDelayed = (delay = 0.2) => ({
  duration: 0.9,
  delay,
  ease: easeOutExpo,
});

/** Tab / panel quick switch. */
export const tabSwitch = { duration: 0.2, ease: easeSmooth };

/** Pulsing animation (looping). */
export const pulseSlow = { duration: 3, repeat: Infinity, ease: 'easeInOut' as const };

/** Pulse variant with delayed phase. */
export const pulseSlowDelayed = (delay = 0.5) => ({
  duration: 3,
  repeat: Infinity,
  ease: 'easeInOut' as const,
  delay,
});

/** Faster pulse for active indicators. */
export const pulseFast = { duration: 2.5, repeat: Infinity, ease: 'easeInOut' as const };

/** Linear loop — for scan lines, progress bars with CSS. */
export const scanLine = { duration: 4, repeat: Infinity, ease: 'linear' as const };

/** Hover lift (scale). */
export const hoverLift = { whileHover: { scale: 1.02 }, transition: micro };

/** Tap press (scale down). */
export const tapPress = { whileTap: { scale: 0.98 }, transition: micro };

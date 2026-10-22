/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Deterministic pseudo-random number generator (Mulberry32).
 * Ensures that all simulation runs, vehicle arrival streams, speed sampling,
 * and stochastic discharge events are 100% reproducible given the same seed.
 */
export class SeededPRNG {
  private initialSeed: number;
  private state: number;

  constructor(seed: number = 42) {
    this.initialSeed = Math.floor(Math.abs(seed)) || 42;
    this.state = this.initialSeed;
  }

  /**
   * Returns a pseudo-random floating-point number in [0, 1)
   */
  public next(): number {
    let t = (this.state += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Returns a random float in [min, max)
   */
  public nextFloat(min: number, max: number): number {
    return min + (max - min) * this.next();
  }

  /**
   * Returns a random integer in [min, max] inclusive
   */
  public nextInt(min: number, max: number): number {
    return Math.floor(this.nextFloat(min, max + 1));
  }

  /**
   * Returns a boolean with probability p of being true
   */
  public nextBool(p: number = 0.5): boolean {
    return this.next() < p;
  }

  /**
   * Pick an item from an array
   */
  public pick<T>(items: readonly T[]): T {
    const idx = this.nextInt(0, items.length - 1);
    return items[idx];
  }

  /**
   * Resets PRNG state back to initial seed or a new seed
   */
  public reset(newSeed?: number): void {
    if (newSeed !== undefined) {
      this.initialSeed = Math.floor(Math.abs(newSeed)) || 42;
    }
    this.state = this.initialSeed;
  }

  /**
   * Get the current seed
   */
  public getSeed(): number {
    return this.initialSeed;
  }
}

// Global default PRNG instance
export const simulationPRNG = new SeededPRNG(1337);

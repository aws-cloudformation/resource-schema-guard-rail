/**
 * Type definitions for Guard Rail VS Code Extension
 */

/**
 * Result of a single guard rule check
 */
export interface GuardRuleResult {
  /** Unique identifier for the check (e.g., "TAG016") */
  check_id: string;
  
  /** Human-readable error or warning message */
  message: string;
  
  /** JSON path to the issue location (e.g., "/properties/Tags") */
  path: string;
}

/**
 * Complete result from Guard Rail CLI execution
 */
export interface GuardRailResult {
  /** List of rule names that passed validation */
  compliant: string[];
  
  /** Map of rule names to their failed checks */
  non_compliant: Record<string, GuardRuleResult[]>;
  
  /** Map of rule names to their warning checks */
  warning: Record<string, GuardRuleResult[]>;
  
  /** List of rule names that were skipped (not applicable) */
  skipped: string[];
}

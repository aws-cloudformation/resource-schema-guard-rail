package com.amazon.guardrail

import com.google.gson.annotations.SerializedName
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.util.Alarm

/**
 * Represents a single rule violation from Guard Rail validation.
 *
 * @property checkId The unique identifier for the rule that was violated
 * @property message The detailed message describing the violation
 * @property path The JSON path where the violation occurred (e.g., "/properties/Tags")
 */
data class GuardRailResult(
    @SerializedName("check_id")
    val checkId: String,
    val message: String,
    val path: String
)

/**
 * Represents the validation results from the Guard Rail CLI for a single file.
 *
 * @property nonCompliant Map of rule names to lists of error violations
 * @property warning Map of rule names to lists of warning violations
 */
data class GuardRailResults(
    @SerializedName("non_compliant")
    val nonCompliant: Map<String, List<GuardRailResult>>?,
    val warning: Map<String, List<GuardRailResult>>?
)

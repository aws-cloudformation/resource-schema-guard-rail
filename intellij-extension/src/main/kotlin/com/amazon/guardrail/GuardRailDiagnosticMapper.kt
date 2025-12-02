package com.amazon.guardrail

import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.intellij.codeInspection.ProblemHighlightType
import com.intellij.json.psi.JsonArray
import com.intellij.json.psi.JsonFile
import com.intellij.lang.annotation.HighlightSeverity
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.editor.colors.CodeInsightColors
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.psi.PsiDocumentManager
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.intellij.json.psi.JsonObject as PsiJsonObject

/**
 * Violation severity type.
 */
enum class ViolationType {
    ERROR,
    WARNING
}

// cli validation results to ProblemDescriptor objects.
// parse JSON output from the cli
class GuardRailDiagnosticMapper {

    private val LOG = Logger.getInstance(GuardRailDiagnosticMapper::class.java)

    // maps validation results from CLI output to diagnostic information
    fun mapResults(cliOutput: String, psiFile: PsiFile): List<DiagnosticInfo> {
        val descriptors = mutableListOf<DiagnosticInfo>()

        try {
            val jsonElement = JsonParser.parseString(cliOutput)
            val jsonObject = jsonElement.asJsonObject

            val guardRailResults = parseValidationResult(jsonObject)

            if (guardRailResults == null) {
                LOG.warn("Could not parse validation result from CLI output")
                return emptyList()
            }

            // Process errors and warnings
            val errorDescriptors = processViolations(guardRailResults.nonCompliant, psiFile, ViolationType.ERROR)
            val warningDescriptors = processViolations(guardRailResults.warning, psiFile, ViolationType.WARNING)

            descriptors.addAll(errorDescriptors)
            descriptors.addAll(warningDescriptors)

            LOG.info("Mapped ${descriptors.size} problem descriptors")
        } catch (e: Exception) {
            LOG.error("Failed to parse CLI output. Output preview: ${cliOutput.take(200)}", e)
        }

        return descriptors
    }

    private fun processViolations(
        violations: Map<String, List<GuardRailResult>>?,
        psiFile: PsiFile,
        type: ViolationType
    ): List<DiagnosticInfo> {
        return violations?.flatMap { (ruleName, violationList) ->
            violationList.map { violation ->
                val lineNumber = extractLineNumber(violation.path, psiFile)
                createDescriptor(lineNumber, ruleName, violation, type)
            }
        } ?: emptyList()
    }

    // parses the validation result from the CLI JSON output
    private fun parseValidationResult(jsonObject: JsonObject): GuardRailResults? {
        try {
            val parseField = { fieldName: String ->
                if (jsonObject.has(fieldName)) {
                    val fieldObject = jsonObject.getAsJsonObject(fieldName)
                    fieldObject.entrySet().associate { (ruleName, violationsJson) ->
                        ruleName to parseViolations(violationsJson)
                    }.filterValues { it.isNotEmpty() }
                } else {
                    emptyMap()
                }
            }

            val nonCompliantMap = parseField("non_compliant")
            val warningMap = parseField("warning")

            return GuardRailResults(nonCompliantMap, warningMap)
        } catch (e: Exception) {
            LOG.error("Failed to parse validation result", e)
            return null
        }
    }

    // parse a list of violations from JSON
    private fun parseViolations(violationsJson: JsonElement): List<GuardRailResult> {
        val violations = mutableListOf<GuardRailResult>()

        try {
            if (violationsJson.isJsonArray) {
                violationsJson.asJsonArray.forEach { violationJson ->
                    if (violationJson.isJsonObject) {
                        val obj = violationJson.asJsonObject
                        val violation = GuardRailResult(
                            checkId = obj.get("check_id")?.asString ?: "",
                            message = obj.get("message")?.asString ?: "",
                            path = obj.get("path")?.asString ?: ""
                        )
                        violations.add(violation)
                    }
                }
            }
        } catch (e: Exception) {
            LOG.error("Failed to parse violations", e)
        }

        return violations
    }

    private fun createDescriptor(
        lineNumber: Int,
        ruleName: String,
        violation: GuardRailResult,
        type: ViolationType
    ): DiagnosticInfo {
        val description = "[${violation.checkId}] ${violation.message}"
        val highlightType = when (type) {
            ViolationType.ERROR -> ProblemHighlightType.ERROR
            ViolationType.WARNING -> ProblemHighlightType.WARNING
        }

        return DiagnosticInfo(
            lineNumber = lineNumber,
            description = description,
            highlightType = highlightType,
            ruleName = ruleName,
            violation = violation
        )
    }

    // extracts the line number from a JSON path in the source file
    fun extractLineNumber(jsonPath: String, psiFile: PsiFile): Int {
        return try {
            val jsonFile = psiFile as? JsonFile ?: return 0
            val segments = jsonPath.split("/").filter { it.isNotEmpty() }
            if (segments.isEmpty()) return 0

            val root = jsonFile.topLevelValue
            val element = navigatePath(root, segments, root) ?: return 0
            val document = PsiDocumentManager.getInstance(psiFile.project).getDocument(psiFile) ?: return 0
            document.getLineNumber(element.textOffset)
        } catch (e: Exception) {
            LOG.error("Failed to extract line number for path '$jsonPath'", e)
            0
        }
    }

    // Recursively navigate through PSI tree following path segments
    private fun navigatePath(element: PsiElement?, segments: List<String>, root: PsiElement?): PsiElement? {
        if (element == null || segments.isEmpty()) return element

        // Resolve $ref if present, substituting the referenced definition
        val current = if (element is PsiJsonObject) {
            resolveRef(element, root) ?: element
        } else {
            element
        }

        val segment = segments.first()
        val remaining = segments.drop(1)

        val next = when {
            // "*" means array definition - navigate to "items"
            segment == "*" && current is PsiJsonObject -> current.findProperty("items")?.value

            // Numeric index - navigate into array
            segment.toIntOrNull() != null && current is JsonArray -> current.valueList.getOrNull(segment.toInt())

            // Property navigation on object
            current is PsiJsonObject -> findProperty(current, segment)

            else -> null
        }

        return navigatePath(next, remaining, root)
    }

    // Resolve $ref to the actual definition object
    private fun resolveRef(obj: PsiJsonObject, root: PsiElement?): PsiJsonObject? {
        val refValue = obj.findProperty("\$ref")?.value?.text?.trim('"') ?: return null
        if (!refValue.startsWith("#/")) return null

        val refSegments = refValue.substring(2).split("/")
        return navigatePath(root, refSegments, root) as? PsiJsonObject
    }

    // Find property in object, checking "properties" wrapper if needed
    private fun findProperty(obj: PsiJsonObject, segment: String): PsiElement? {
        // Try direct access first
        obj.findProperty(segment)?.value?.let { return it }

        // Try inside "properties" wrapper
        return obj.findProperty("properties")?.value?.let { propsValue ->
            (propsValue as? PsiJsonObject)?.findProperty(segment)?.value
        }
    }
}

data class DiagnosticInfo(
    val lineNumber: Int,
    val description: String,
    val highlightType: ProblemHighlightType,
    val ruleName: String,
    val violation: GuardRailResult
) {
    val severity: HighlightSeverity
        get() = when (highlightType) {
            ProblemHighlightType.ERROR -> HighlightSeverity.ERROR
            ProblemHighlightType.WARNING -> HighlightSeverity.WARNING
            else -> HighlightSeverity.WEAK_WARNING
        }

    val textAttributes: com.intellij.openapi.editor.colors.TextAttributesKey?
        get() = when (highlightType) {
            ProblemHighlightType.ERROR -> GUARD_RAIL_ERROR_ATTRIBUTES
            ProblemHighlightType.WARNING -> GUARD_RAIL_WARNING_ATTRIBUTES
            else -> null // No text attributes for default case
        }

    companion object {
        // Custom text attributes for Guard Rail errors.
        // Provides a red tint background for the entire line.
        val GUARD_RAIL_ERROR_ATTRIBUTES = TextAttributesKey.createTextAttributesKey(
            "GUARD_RAIL_ERROR",
            CodeInsightColors.ERRORS_ATTRIBUTES
        )

        // Custom text attributes for Guard Rail warnings.
        // Provides a blue tint background for the entire line.
        val GUARD_RAIL_WARNING_ATTRIBUTES = TextAttributesKey.createTextAttributesKey(
            "GUARD_RAIL_WARNING",
            CodeInsightColors.WARNINGS_ATTRIBUTES
        )
    }
}

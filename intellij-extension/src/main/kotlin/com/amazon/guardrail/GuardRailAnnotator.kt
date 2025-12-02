package com.amazon.guardrail

import com.intellij.lang.annotation.AnnotationHolder
import com.intellij.lang.annotation.ExternalAnnotator
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.util.TextRange
import com.intellij.psi.PsiFile

/**
 * External annotator that provides real-time validation for JSON schema files.
 * * This annotator:
 * - Collects information about JSON files in the editor
 * - Triggers validation through the GuardRailValidationService
 * - Applies visual annotations (highlights, gutter icons, tooltips) to the editor
 * - Integrates with IntelliJ's inspection system for the Problems tool window
 * * The annotator follows IntelliJ's three-phase annotation process:
 * 1. collectInformation: Runs on UI thread, returns PsiFile for JSON files
 * 2. doAnnotate: Runs on background thread, performs validation and returns diagnostics
 * 3. apply: Runs on UI thread, creates annotations in the editor
 * * Integration with Problems Tool Window:
 * Annotations created by this annotator are automatically registered with IntelliJ's
 * inspection system and appear in the Problems tool window. The integration provides:
 * - Proper categorization (errors vs warnings)
 * - Navigation from Problems window to diagnostic location
 * - Filtering and grouping capabilities
 * - Automatic updates when diagnostics change
 * * The key to this integration is using HighlightSeverity (ERROR/WARNING) and
 * ProblemHighlightType, which IntelliJ uses to populate the Problems window.
 */
class GuardRailAnnotator : ExternalAnnotator<PsiFile, List<DiagnosticInfo>>() {

    private val LOG = Logger.getInstance(GuardRailAnnotator::class.java)

    // Collects information on annotated file
    // A UI thread
    override fun collectInformation(file: PsiFile): PsiFile? {
        return file.takeIf { it.fileType.name == "JSON" }
    }

    // Validates and preps diagnostic info
    // Runs on the background thread and triggers validation
    override fun doAnnotate(collectedInfo: PsiFile): List<DiagnosticInfo>? {
        // virtualFile is Intellij's representation of a file on disk
        // we need it to get file path to pass to cli
        val file = collectedInfo.virtualFile ?: return null
        val project = collectedInfo.project

        LOG.info("doAnnotate called for: ${file.name} (path: ${file.path})")

        try {
            // Save the document first so CLI can read it
            val document = com.intellij.openapi.application.ApplicationManager.getApplication().runReadAction<com.intellij.openapi.editor.Document?> {
                com.intellij.openapi.fileEditor.FileDocumentManager.getInstance().getDocument(file)
            }

            if (document != null) {
                // use invokeAndWait because doAnnotate running on the background thread
                // but saving a file runs on the UI thread
                // (it's a thread switch ;)
                com.intellij.openapi.application.ApplicationManager.getApplication().invokeAndWait {
                    // saves doc on disk - writes in-memory changes to the physical file
                    com.intellij.openapi.fileEditor.FileDocumentManager.getInstance().saveDocument(document)
                }
                LOG.info("Document saved for: ${file.name}")
            }

            val validationService = GuardRailValidationService.getInstance()

            // Trigger validation and get results synchronously
            LOG.info("Triggering validation for: ${file.name}")
            val diagnostics = validationService.validateFileAndGetResults(file, project)

            LOG.info("Retrieved ${diagnostics.size} diagnostics for: ${file.name}")

            if (diagnostics.isNotEmpty()) {
                diagnostics.forEachIndexed { index, diag ->
                    LOG.info("  Diagnostic $index: line=${diag.lineNumber}, checkId=${diag.violation.checkId}")
                }
            }

            return diagnostics
        } catch (e: Exception) {
            LOG.error("Error during annotation", e)
            return null
        }
    }

    // apply uses diagnostic results to apply annotations
    // (it's a UI thread ;)
    // for diagnostics it
    //   - highlights line with appropriate decorations
    //   - adds error/warning marker
    //   - adds tooltip
    override fun apply(
        file: PsiFile,
        annotationResult: List<DiagnosticInfo>,
        holder: AnnotationHolder
    ) {
        LOG.info("apply called for: ${file.name} with ${annotationResult.size} diagnostics")

        if (annotationResult.isEmpty()) {
            LOG.info("No diagnostics to apply for: ${file.name}")
            return
        }

        LOG.info("Applying ${annotationResult.size} annotations to: ${file.name}")

        val document = file.viewProvider.document
        if (document == null) {
            LOG.warn("No document available for: ${file.name}")
            return
        }

        LOG.info("Document has ${document.lineCount} lines")

        annotationResult.forEach { diagnostic ->
            try {
                // Get the line range
                val lineNumber = diagnostic.lineNumber.coerceIn(0, document.lineCount - 1)
                val lineStartOffset = document.getLineStartOffset(lineNumber)
                val lineEndOffset = document.getLineEndOffset(lineNumber)
                val textRange = TextRange(lineStartOffset, lineEndOffset)

                val annotationBuilder = holder.newAnnotation(diagnostic.severity, diagnostic.description)
                    .range(textRange)
                    .tooltip(formatTooltip(diagnostic))
                    .highlightType(diagnostic.highlightType)

                // Apply text attributes only if present (not for default/weak warnings)
                diagnostic.textAttributes?.let { annotationBuilder.textAttributes(it) }

                // Create the annotation
                // This will automatically add:
                // - Gutter icon based on severity
                // - Error stripe in scrollbar
                // - Background highlighting
                // - Entry in Problems tool window (via inspection system integration)
                annotationBuilder.create()

                LOG.info("Applied annotation at line $lineNumber: ${diagnostic.violation.checkId} (severity: ${diagnostic.severity})")
            } catch (e: Exception) {
                LOG.error("Failed to apply annotation for diagnostic: ${diagnostic.description}", e)
            }
        }
    }

    private fun formatTooltip(diagnostic: DiagnosticInfo): String {
        return buildString {
            append("<html>")
            append("<b>Check ID:</b> (${diagnostic.violation.checkId})<br>")
            append("<b>Message:</b> ${diagnostic.violation.message}<br>")
            append("<b>Description:</b> ${diagnostic.description}<br>")
            append("<b>Rule Name:</b> [${diagnostic.ruleName}]<br>")
            append("</html>")
        }
    }
}

package com.amazon.guardrail

import com.intellij.codeInsight.daemon.LineMarkerInfo
import com.intellij.codeInsight.daemon.LineMarkerProvider
import com.intellij.icons.AllIcons
import com.intellij.json.psi.JsonFile
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.editor.markup.GutterIconRenderer
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindowManager
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.intellij.ui.JBColor
import com.intellij.util.ui.ColorizeProxyIcon
import java.awt.Color
import java.awt.Component
import java.awt.Graphics
import javax.swing.Icon

/**
 * Provides gutter icons for JSON schema files that allow executing Guard Rail validation
 * directly from the editor.
 * * The gutter icon appears at line 1 of JSON files and executes a placeholder command
 * when clicked. Results are displayed in the Guard Rail Output tool window.
 */
class GuardRailGutterIconProvider : LineMarkerProvider {

    private val LOG = Logger.getInstance(GuardRailGutterIconProvider::class.java)

    private val orangeIcon: Icon by lazy {
        val baseIcon = AllIcons.RunConfigurations.TestState.Run // type of the icon
        val orangeColor = JBColor(Color(255, 140, 0), Color(255, 165, 0))
        val coloredIcon = ColorizeProxyIcon.Simple(baseIcon, orangeColor)

        object : Icon {
            private val text = "Run Checks"

            override fun paintIcon(c: Component?, g: Graphics, x: Int, y: Int) {
                coloredIcon.paintIcon(c, g, x, y)
                g.color = orangeColor
                g.font = g.font.deriveFont(10f)
                g.drawString(text, x + coloredIcon.iconWidth + 2, y + 12)
            }

            override fun getIconWidth(): Int {
                // calc width based on text length to prevent cutoff
                // ~6 pixels per character + icon width + spacing
                return coloredIcon.iconWidth + (text.length * 6) + 4
            }

            override fun getIconHeight(): Int = coloredIcon.iconHeight
        }
    }

    override fun getLineMarkerInfo(element: PsiElement): LineMarkerInfo<*>? {
        // Only process the root element of JSON files
        val file = element.containingFile
        if (file !is JsonFile) {
            return null
        }

        // shows icon for the first child element of the file
        if (element != file.firstChild) {
            return null
        }

        // creates line marker at line 1
        return LineMarkerInfo(
            element,
            element.textRange,
            orangeIcon,
            { "Run Guard Rail Validation - Click to compare with CloudFormation schema" },
            { _, elt ->
                executeCommand(elt.project, file)
            },
            GutterIconRenderer.Alignment.LEFT,
            { "Run Guard Rail Validation" }
        )
    }

    // fetches schema (cfn)
    // saves it to a temporary file
    // runs guard-rail validation
    private fun executeCommand(project: Project, file: PsiFile) {
        val virtualFile = file.virtualFile ?: return
        val localSchemaPath = virtualFile.path

        LOG.info("Starting Guard Rail validation for: $localSchemaPath")

        // flush the output terminal
        val outputPanel = GuardRailOutputToolWindowFactory.getOutputPanel(project)
        outputPanel?.clear()

        val startTime = System.currentTimeMillis()
        var tempFile: java.io.File? = null

        try {
            // fetch schema
            LOG.info("Fetching schema from CloudFormation")
            val schemaFetcher = CloudFormationSchemaFetcher()
            val retrievedSchema = schemaFetcher.fetchSchema(localSchemaPath)

            if (retrievedSchema == null) {
                LOG.error("Failed to fetch schema from CloudFormation")
                outputPanel?.displayResults(
                    command = "guard-rail validation",
                    stdout = "",
                    stderr = "Failed to fetch schema from CloudFormation. Check logs for details.",
                    exitCode = 1,
                    executionTime = System.currentTimeMillis() - startTime
                )
                val toolWindow = ToolWindowManager.getInstance(project).getToolWindow("GuardRail Output")
                toolWindow?.show()
                return
            }

            // Step 2: Save retrieved schema to temporary file in project directory
            val projectDir = project.basePath ?: throw IllegalStateException("Project base path is null")
            val projectDirFile = java.io.File(projectDir)

            tempFile = java.io.File.createTempFile("cfn-schema-", ".json", projectDirFile)
            tempFile.writeText(retrievedSchema)
            LOG.info("Saved retrieved schema to temporary file: ${tempFile.absolutePath}")

            // Step 3: Execute guard-rail stateful validation using GuardRailCliExecutor
            val executor = GuardRailCliExecutor(projectDir)
            val processOutput = executor.executeStateful(tempFile.absolutePath, localSchemaPath)

            val executionTime = System.currentTimeMillis() - startTime
            val commandString = "guard-rail --schema file://${tempFile.absolutePath} --schema file://$localSchemaPath --stateful --format"

            // Display results
            outputPanel?.displayResults(
                command = commandString,
                stdout = processOutput.stdout,
                stderr = processOutput.stderr,
                exitCode = processOutput.exitCode,
                executionTime = executionTime
            )

            val toolWindow = ToolWindowManager.getInstance(project).getToolWindow("GuardRail Output")
            toolWindow?.show()

            LOG.info("Guard Rail validation completed | Exit code: ${processOutput.exitCode} | Duration: ${executionTime}ms")
        } catch (e: Exception) {
            LOG.error("Error during Guard Rail validation", e)

            outputPanel?.displayResults(
                command = "guard-rail validation",
                stdout = "",
                stderr = "Exception: ${e.message}\n${e.stackTraceToString()}",
                exitCode = 1,
                executionTime = System.currentTimeMillis() - startTime
            )

            val toolWindow = ToolWindowManager.getInstance(project).getToolWindow("GuardRail Output")
            toolWindow?.show()
        } finally {
            // Clean up temporary file
            tempFile?.delete()
            if (tempFile != null) {
                LOG.info("Deleted temporary file: ${tempFile.absolutePath}")
            }
        }
    }
}

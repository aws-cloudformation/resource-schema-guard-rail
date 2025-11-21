package com.amazon.guardrail

import com.intellij.openapi.project.Project
import java.awt.BorderLayout
import java.awt.Font
import java.text.SimpleDateFormat
import java.util.Date
import javax.swing.JPanel
import javax.swing.JScrollPane
import javax.swing.JTextArea

/**
 * Panel for displaying Guard Rail command execution results.
 * 
 * This panel shows:
 * - The command that was executed
 * - Execution timestamp
 * - Standard output
 * - Standard error output
 * 
 * All output is displayed in a monospace font for better readability.
 */
class GuardRailOutputPanel(private val project: Project) {
    
    private val outputArea = JTextArea()
    private val panel = JPanel(BorderLayout())
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
    
    init {
        // configure text area
        outputArea.isEditable = false
        outputArea.font = Font("Monospaced", Font.PLAIN, 12)
        outputArea.lineWrap = false
        val scrollPane = JScrollPane(outputArea)
        panel.add(scrollPane, BorderLayout.CENTER)
    }
    
    // returns the main panel component for display in the tool window
    fun getComponent(): JPanel = panel

    fun displayResults(
        command: String,
        stdout: String,
        stderr: String,
        exitCode: Int,
        executionTime: Long
    ) {
        val timestamp = dateFormat.format(Date())
        val formattedOutput = formatOutput(command, timestamp, stdout, stderr, exitCode, executionTime)
        
        outputArea.text = formattedOutput
        outputArea.caretPosition = 0 // scroll to top
    }

    fun clear() {
        outputArea.text = ""
    }
    
    private fun formatOutput(
        command: String,
        timestamp: String,
        stdout: String,
        stderr: String,
        exitCode: Int,
        executionTime: Long
    ): String {
        val builder = StringBuilder()
        
        // header section
        builder.append("=" .repeat(80)).append("\n")
        builder.append("Guard Rail Command Execution\n")
        builder.append("=" .repeat(80)).append("\n\n")
        
        // command details
        builder.append("Command: $command\n")
        builder.append("Executed: $timestamp\n")
        builder.append("Duration: ${executionTime}ms\n")
        builder.append("Exit Code: $exitCode\n")
        builder.append("\n")
        
        // standard output section
        builder.append("-" .repeat(80)).append("\n")
        builder.append("Standard Output:\n")
        builder.append("-" .repeat(80)).append("\n")
        if (stdout.isNotEmpty()) {
            builder.append(stdout)
            if (!stdout.endsWith("\n")) {
                builder.append("\n")
            }
        } else {
            builder.append("(no output)\n")
        }
        builder.append("\n")
        
        // Standard error section
        builder.append("-" .repeat(80)).append("\n")
        builder.append("Standard Error:\n")
        builder.append("-" .repeat(80)).append("\n")
        if (stderr.isNotEmpty()) {
            builder.append(stderr)
            if (!stderr.endsWith("\n")) {
                builder.append("\n")
            }
        } else {
            builder.append("(no errors)\n")
        }
        builder.append("\n")
        
        builder.append("=" .repeat(80)).append("\n")
        
        return builder.toString()
    }
}

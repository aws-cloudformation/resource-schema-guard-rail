package com.amazon.guardrail

import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.CapturingProcessHandler
import com.intellij.execution.process.ProcessOutput
import com.intellij.notification.Notification
import com.intellij.notification.NotificationType
import com.intellij.notification.Notifications
import com.intellij.openapi.diagnostic.Logger
import java.io.IOException

class GuardRailCliExecutor(private val projectBasePath: String) {

    private val LOG = Logger.getInstance(GuardRailCliExecutor::class.java)
    private val gson = Gson()
    private val TIMEOUT_SECONDS = 10L

    // execute resource-schema-guard-rail cli tool (stateless mode with --json)
    fun executeStateless(schemaPath: String): List<GuardRailResults> {
        val startTime = System.currentTimeMillis()

        LOG.info("Starting Guard Rail validation | Schema path: $schemaPath | Timestamp: $startTime")

        try {
            val commandLine = buildCommandLine(schemaPath)
            val processHandler = CapturingProcessHandler(commandLine)

            // sets 10 ms timeout
            val processOutput = processHandler.runProcess((TIMEOUT_SECONDS * 1000).toInt())

            if (processOutput.isTimeout) {
                LOG.error("Guard Rail validation timed out after $TIMEOUT_SECONDS seconds")
                showNotification(
                    "Guard Rail Validation Timeout",
                    "Validation timed out after $TIMEOUT_SECONDS seconds. File may be too large or complex.",
                    NotificationType.ERROR
                )
                return emptyList()
            }

            // Get exit code
            val exitCode = processOutput.exitCode
            LOG.info("Process completed with exit code: $exitCode | Execution time: ${System.currentTimeMillis() - startTime}ms")

            // Log captured output
            val stdout = processOutput.stdout
            val stderr = processOutput.stderr
            LOG.info("Captured stdout length: ${stdout.length} | stderr length: ${stderr.length}")

            if (stdout.isNotEmpty()) {
                LOG.info("Stdout preview: ${stdout.take(200)}")
            }
            if (stderr.isNotEmpty()) {
                LOG.info("Stderr preview: ${stderr.take(200)}")
            }

            return handleProcessCompletion(exitCode, stdout, stderr)
        } catch (e: IOException) {
            LOG.error("IO error executing Guard Rail CLI", e)
            return emptyList()
        } catch (e: Exception) {
            LOG.error("Unexpected error during CLI execution", e)
            showNotification(
                "Guard Rail Validation Error",
                "Unexpected error: ${e.message}",
                NotificationType.ERROR
            )
            return emptyList()
        }
    }

    // command line builder
    private fun buildCommandLine(schemaPath: String): GeneralCommandLine {
        return GeneralCommandLine().apply {
            exePath = "guard-rail"
            addParameter("--schema")
            addParameter("file://$schemaPath")
            addParameter("--json")
            withWorkDirectory(projectBasePath)
        }
    }

    // handles process completion based on exit code.
    private fun handleProcessCompletion(exitCode: Int, stdout: String, stderr: String): List<GuardRailResults> {
        return when (exitCode) {
            0, 1 -> {
                // Exit codes 0 and 1 are acceptable (0 = no issues, 1 = issues found)
                parseOutput(stdout, stderr)
            }
            else -> {
                LOG.error("Guard Rail CLI exited with code $exitCode | Stderr: ${stderr.take(500)}")
                showNotification(
                    "Guard Rail Validation Failed",
                    "CLI exited with code $exitCode. Error: ${stderr.take(200)}",
                    NotificationType.ERROR
                )
                emptyList()
            }
        }
    }

    // parse JSON output from cli
    private fun parseOutput(stdout: String, stderr: String): List<GuardRailResults> {
        // The cli writes output to stderr, not stdout
        var jsonOutput = if (stderr.trim().isNotEmpty() && stderr.trim().startsWith("[")) {
            stderr
        } else if (stdout.trim().isNotEmpty() && stdout.trim().startsWith("[")) {
            stdout
        } else if (stderr.trim().isNotEmpty()) {
            stderr
        } else {
            stdout
        }

        if (jsonOutput.trim().isEmpty()) {
            LOG.warn("No output from Guard Rail CLI")
            return emptyList()
        }

        // translate Python syntax to JSON (single quotes to double quotes)
        // cli outputs Python dict/list syntax, not valid JSON
        // TODO: return proper good json
        jsonOutput = jsonOutput
            .replace("'", "\"")

        return try {
            val results = gson.fromJson(jsonOutput, Array<GuardRailResults>::class.java)
            LOG.info("Successfully parsed ${results.size} validation results")
            results.toList()
        } catch (e: JsonSyntaxException) {
            LOG.error("Failed to parse Guard Rail output as JSON", e)
            LOG.error("Output preview: ${jsonOutput.take(500)}")

            showNotification(
                "Guard Rail Parsing Error",
                "Failed to parse CLI output. CLI may have produced invalid JSON.",
                NotificationType.ERROR
            )

            emptyList()
        }
    }

    // execute resource-schema-guard-rail cli tool (stateful mode with --format)
    fun executeStateful(retrievedSchemaPath: String, localSchemaPath: String): ProcessOutput {
        val startTime = System.currentTimeMillis()

        LOG.info("Starting Guard Rail stateful validation | Retrieved: $retrievedSchemaPath | Local: $localSchemaPath")

        try {
            val logFilePath = java.io.File(projectBasePath, "guard-rail.log").absolutePath

            val commandLine = GeneralCommandLine().apply {
                exePath = "guard-rail"
                addParameter("--schema")
                addParameter("file://$retrievedSchemaPath")
                addParameter("--schema")
                addParameter("file://$localSchemaPath")
                addParameter("--stateful")
                addParameter("--format")
                withWorkDirectory(projectBasePath)
                withEnvironment("GUARD_RAIL_LOG", logFilePath)
                withEnvironment("COLUMNS", "200") // Set wide terminal width to prevent truncation
            }

            val commandString = "guard-rail --schema file://$retrievedSchemaPath --schema file://$localSchemaPath --stateful --format"
            LOG.info("Executing command: $commandString")
            LOG.info("Working directory: $projectBasePath")
            LOG.info("Log file: $logFilePath")

            val processHandler = CapturingProcessHandler(commandLine)
            val processOutput = processHandler.runProcess(30000) // 30 second timeout

            val executionTime = System.currentTimeMillis() - startTime
            LOG.info("Guard Rail stateful validation completed | Exit code: ${processOutput.exitCode} | Duration: ${executionTime}ms")

            return processOutput
        } catch (e: Exception) {
            LOG.error("Error during Guard Rail stateful validation", e)
            throw e
        }
    }

    private fun showNotification(title: String, content: String, type: NotificationType) {
        val notification = Notification(
            "Guard Rail",
            title,
            content,
            type
        )
        Notifications.Bus.notify(notification)
    }
}

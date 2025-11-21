package com.amazon.guardrail

import com.google.gson.Gson
import com.intellij.notification.Notification
import com.intellij.notification.NotificationType
import com.intellij.notification.Notifications
import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.openapi.wm.WindowManager
import com.intellij.psi.PsiManager
import com.intellij.util.Alarm
import java.util.concurrent.ConcurrentHashMap

/**
 * Application-level service that manages Guard Rail validation requests and state.
 * 
 * This service is responsible for:
 * - Orchestrating the validation workflow
 * - Managing validation state per file
 * - Executing validation in background threads
 * - Coordinating between CLI executor and diagnostic mapper
 * - Handling file size checks and validation skipping
 * - Clearing diagnostics when appropriate
 */
@Service
class GuardRailValidationService : Disposable {
    
    private val LOG = Logger.getInstance(GuardRailValidationService::class.java)
    
    // Centralized cache that stores diagnostics per file
    // must be thread-safe as multiple UI threads access it 
    private val centralizedDiagnosticsCache = ConcurrentHashMap<String, List<DiagnosticInfo>>()
    
    // Reusable mapper instance (stateless, thread-safe)
    private val diagnosticMapper = GuardRailDiagnosticMapper()
    
    // Gson instance for JSON serialization
    private val gson = Gson()
    
    private val MAX_FILE_SIZE_BYTES = 1073741824L // (1GB)
    
    
    fun validateFileAndGetResults(file: VirtualFile, project: Project): List<DiagnosticInfo> =
        file.takeIf { it.isInLocalFileSystem } // only run validation if file physically exists
                                               // run cli `guard-rail --schema file://..`
                                               // TODO: allow in-memory files cli can accepts json payload
            ?.takeIf { it.length <= MAX_FILE_SIZE_BYTES } // skip validation on large files
            ?.let { validFile ->
                LOG.info("Executing validation for: ${validFile.path}")
                runCatching {
                    performValidation(validFile, project, validFile.path)
                    getDiagnostics(validFile)
                }.getOrElse { e ->
                    LOG.error("Validation error for ${validFile.path}", e)
                    handleValidationError(validFile.path, "Unexpected error: ${e.message}")
                    emptyList()
                }
            } ?: emptyList<DiagnosticInfo>().also {
                LOG.info("Skipping validation for ${file.path} | file size: (${file.length} bytes) | in-memory ${file.isInLocalFileSystem}")
            }
    
    // manual action entry point
    fun validateFile(file: VirtualFile, project: Project) {
        ApplicationManager.getApplication().executeOnPooledThread {
            validateFileAndGetResults(file, project)
        }
    }
    
    private fun performValidation(file: VirtualFile, project: Project, filePath: String) {
        val startTime = System.currentTimeMillis()
        
        try {
            // Get project base path
            val projectBasePath = project.basePath
            if (projectBasePath == null) {
                LOG.error("Project base path is null")
                handleValidationError(filePath, "Project base path not available")
                return
            }
            
            val executor = GuardRailCliExecutor(projectBasePath)
            val results = executor.executeStateless(filePath)
            
            if (results.isEmpty()) {
                LOG.warn("CLI execution returned no results")
                handleValidationError(filePath, "No validation results")
                return
            }
            
            // Get PSI file for diagnostic mapping
            val psiFile = ApplicationManager.getApplication().runReadAction<com.intellij.psi.PsiFile?> {
                PsiManager.getInstance(project).findFile(file)
            }
            
            if (psiFile == null) {
                LOG.error("Could not get PSI file for: $filePath")
                handleValidationError(filePath, "Could not access file structure")
                return
            }
            
            // Map results to diagnostics using functional approach
            val diagnostics = results.flatMap { validationResult ->
                diagnosticMapper.mapResults(buildJsonOutput(validationResult), psiFile)
            }
            
            // Store diagnostics for the file
            this.centralizedDiagnosticsCache[filePath] = diagnostics
            LOG.info("Stored ${diagnostics.size} diagnostics for: $filePath")
            
            // Count errors and warnings
            val errorCount = diagnostics.count { it.highlightType == com.intellij.codeInspection.ProblemHighlightType.ERROR }
            val warningCount = diagnostics.count { it.highlightType == com.intellij.codeInspection.ProblemHighlightType.WARNING }
            
            LOG.info("Validation completed for: $filePath - Total: ${diagnostics.size}, Errors: $errorCount, Warnings: $warningCount, Time: ${System.currentTimeMillis() - startTime}ms")
            
            // Update UI on UI thread
            ApplicationManager.getApplication().invokeLater {
                LOG.info("Updating UI for: $filePath")
                
                // Update status bar widget
                updateStatusBarWidget(project, errorCount, warningCount)
                LOG.info("Status bar widget update called")
                
                // Trigger annotator refresh by restarting daemon
                com.intellij.codeInsight.daemon.DaemonCodeAnalyzer.getInstance(project).restart(psiFile)
                LOG.info("Daemon code analyzer restarted")
                
                LOG.info("UI update completed for: $filePath")
            }
            
        } catch (e: Exception) {
            LOG.error("Error during validation", e)
            handleValidationError(filePath, e.message ?: "Unknown error")
        }
    }
    
    // translate to json
    private fun buildJsonOutput(validationResult: GuardRailResults): String = gson.toJson(validationResult)

    private fun handleValidationError(filePath: String, error: String) {
        LOG.error("Validation error for $filePath: $error")
        clearDiagnostics(filePath)
    }

    
    private fun getDiagnostics(filePath: String): List<DiagnosticInfo> = centralizedDiagnosticsCache[filePath] ?: emptyList()
    
    fun getDiagnostics(file: VirtualFile): List<DiagnosticInfo> {
        LOG.info("getDiagnostics(VirtualFile): ${file.path}")
        return getDiagnostics(file.path)
    }
    
    private fun clearDiagnostics(filePath: String) {
        LOG.info("Clearing diagnostics for: $filePath")
        centralizedDiagnosticsCache.remove(filePath)
    }
    
    private fun updateStatusBarWidget(project: Project, errorCount: Int, warningCount: Int) {
        LOG.info("updateStatusBarWidget called: errors=$errorCount, warnings=$warningCount")
        
        val statusBar = WindowManager.getInstance().getStatusBar(project)
        LOG.info("Status bar instance: ${statusBar != null}")
        
        if (statusBar != null) {
            val widget = statusBar.getWidget(GuardRailStatusWidget.ID)
            LOG.info("Widget found: ${widget != null}, type: ${widget?.javaClass?.simpleName}")
            
            if (widget is GuardRailStatusWidget) {
                widget.updateStatus(errorCount, warningCount)
                LOG.info("Status bar widget updated successfully: errors=$errorCount, warnings=$warningCount")
            } else {
                LOG.warn("Widget is not GuardRailStatusWidget type: ${widget?.javaClass?.name}")
            }
        } else {
            LOG.warn("Status bar not found for project: ${project.name}")
        }
    }
    
    override fun dispose() {
        LOG.info("Disposing GuardRailValidationService")
        centralizedDiagnosticsCache.clear()
    }
    
    companion object {
        /**
         * Gets the validation service instance.
         * 
         * @return The GuardRailValidationService instance
         */
        fun getInstance(): GuardRailValidationService {
            return ApplicationManager.getApplication().getService(GuardRailValidationService::class.java)
        }
    }
}
